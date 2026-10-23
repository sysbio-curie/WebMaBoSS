from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser

from django.core.files import File
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse, FileResponse

from django.conf import settings
from django.db import transaction
from api.views.HasModel import HasModel
from api.views.HasMaBoSSSimulation import HasMaBoSSSimulation
from api.serializers import MaBoSSSimulationSerializer
from api.models import LogicalModel, MaBoSSSimulation, Project
from api.models.common import clean_guest_account
from django.contrib.auth.models import User
from threading import Thread
from os.path import join, exists, splitext, basename
from os import remove
from json import loads, dumps
import ginsim
import maboss
from api.views.commons.parse import parseIstates,dumpIstates
from time import time
from collections import OrderedDict

# The observed graph has a state per combination of its nodes : 2^n of them, and up to 4^n transitions
MAX_OBSERVED_NODES = 8


def in_observed_graph(node):
	""" Whether a node of a MaBoSS model is in the observed graph (as read in a cfg, it can be a string) """
	return str(node.in_graph).lower() not in ["false", "0", "0.0"]


def sparse_observed_graph(table, nodes):
	""" The observed graph (probabilities of the transitions, from the rows to the columns), without the zeros """
	edges = [
		[source, target, round(float(proba), 6)]
		for source, row in table.iterrows() for target, proba in row.items() if proba > 0
	]
	visited = set(state for edge in edges for state in edge[:2])
	return {
		'nodes': nodes,
		'states': [state for state in table.index if state in visited],
		'edges': edges
	}


class MaBoSSSimulationView(HasModel):

	# Anonymous users can run simulations on the demo models
	anonymous_methods = HasModel.anonymous_methods + ('POST',)

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)
		simulations = MaBoSSSimulation.objects.filter(model=self.model)
		serializer = MaBoSSSimulationSerializer(simulations, many=True)
		return Response(serializer.data)

	def post(self, request, project_id, model_id):
		
		HasModel.load(self, request, project_id, model_id)

		# Without it, the observed graph is the one of the model
		observed_nodes = None
		if 'observedGraphNodes' in request.POST:
			observed_nodes = [key for key, value in loads(request.POST['observedGraphNodes']).items() if value]

			if len(observed_nodes) > MAX_OBSERVED_NODES:
				return Response(
					{'error': "You can only select up to %d nodes for the observed graph" % MAX_OBSERVED_NODES},
					status=status.HTTP_400_BAD_REQUEST
				)
			if len(observed_nodes) > 0 and request.POST.get('serverHost') is not None:
				return Response(
					{'error': "The observed graph is only available for the simulations run locally"},
					status=status.HTTP_400_BAD_REQUEST
				)

		if self.model.format == LogicalModel.ZGINML:
			path = join(settings.MEDIA_ROOT, self.model.file.path)
			ginsim_model = ginsim.load(path)
			maboss_model = ginsim.to_maboss(ginsim_model)

			tmp_bnd_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".bnd")
			bnd_file = open(tmp_bnd_path, 'w')
			maboss_model.print_bnd(out=bnd_file)
			bnd_file.close()

			tmp_cfg_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".cfg")
			cfg_file = open(tmp_cfg_path, 'w')
			maboss_model.print_cfg(out=cfg_file)
			cfg_file.close()

			maboss_simulation = MaBoSSSimulation(
				project=self.project,
				model=self.model,
				name=request.POST['name'],
				bnd_file=File(open(tmp_bnd_path, 'rb'), name=basename(tmp_bnd_path)),
				cfg_file=File(open(tmp_cfg_path, 'rb'), name=basename(tmp_cfg_path)),
				status=MaBoSSSimulation.BUSY
			)
			maboss_simulation.save()

			remove(tmp_bnd_path)
			remove(tmp_cfg_path)

		elif self.model.format == LogicalModel.MABOSS:

			bnd_path = join(settings.MEDIA_ROOT, self.model.bnd_file.path)
			cfg_path = join(settings.MEDIA_ROOT, self.model.cfg_file.path)

			maboss_simulation = MaBoSSSimulation(
				project=self.project,
				model=self.model,
				name=request.POST['name'],
				bnd_file=File(open(bnd_path, 'rb'), name=basename(bnd_path)),
				cfg_file=File(open(cfg_path, 'rb'), name=basename(cfg_path)),
				status=MaBoSSSimulation.BUSY
			)
			maboss_simulation.save()

			maboss_model = maboss.load(bnd_path, cfg_path)
	
		elif self.model.format == LogicalModel.SBML:
			
			maboss_model = self.getMaBoSSModel()
			
			tmp_bnd_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".bnd")
			bnd_file = open(tmp_bnd_path, 'w')
			maboss_model.print_bnd(out=bnd_file)
			bnd_file.close()

			tmp_cfg_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".cfg")
			cfg_file = open(tmp_cfg_path, 'w')
			maboss_model.print_cfg(out=cfg_file)
			cfg_file.close()

			maboss_simulation = MaBoSSSimulation(
				project=self.project,
				model=self.model,
				name=request.POST['name'],
				bnd_file=File(open(tmp_bnd_path, 'rb'), name=basename(tmp_bnd_path)),
				cfg_file=File(open(tmp_cfg_path, 'rb'), name=basename(tmp_cfg_path)),
				status=MaBoSSSimulation.BUSY
			)
			maboss_simulation.save()

			remove(tmp_bnd_path)
			remove(tmp_cfg_path)
			
			
		else:
			return HttpResponse(status=500)
			
		cfg_settings = loads(request.POST['settings'])
		maboss_model.param.update(cfg_settings)
		maboss_model.param['thread_count'] = 6
		maboss_model.param['time_tick'] = float(maboss_model.param['max_time'])/100

		mutations = loads(request.POST['mutations'])
		for var, mutation in mutations.items():
			maboss_model.mutate(var, mutation)

		maboss_model.network.set_output(
			[key for key, value in loads(request.POST['outputVariables']).items() if value]
		)

		if observed_nodes is not None:
			maboss_model.network.set_observed_graph_nodes(observed_nodes)

		for var, istate in parseIstates(request.POST['initialStates']).items():
			maboss_model.network.set_istate(var, istate)

		maboss_simulation.update_model(maboss_model)

		server_host = request.POST.get('serverHost')
		server_port = request.POST.get('serverPort')

		thread = Thread(target=run_simulation, args=(maboss_model, maboss_simulation.id, server_host, server_port))
		thread.start()
		
		# Here we want to check if there are some models we need to clean
		if request.user.is_anonymous:
			clean_guest_account()
				
		return Response({'simulation_id': maboss_simulation.id}, status=status.HTTP_200_OK)

def run_simulation(maboss_model, maboss_simulation_id, server_host, server_port):

	try:
		# t0 = time()
		# print("Started thread")
		if server_host is None:
			res = maboss_model.run()
		else:
			mbcli = maboss.MaBoSSClient(server_host, int(server_port))
			res = mbcli.run(maboss_model)
			mbcli.close()

		# t1 = time()
		# print("Simulation done : %.2gs" % (t1-t0))
		fixed_points = res.get_fptable()
		if fixed_points is not None:
			fixed_points_json = fixed_points.to_json()
		else:
			fixed_points_json = "{}"
		# t2 = time()
		# print("Loaded fixed points : %.2gs" % (t2-t1))
		states_probtraj = res.get_states_probtraj()
		states_probtraj_json = states_probtraj.to_json()
		# t3 = time()
		# print("Loaded probtraj : %.2gs" % (t3-t2))
		
		
		nodes_probtraj = res.get_nodes_probtraj()
		nodes_probtraj_json = nodes_probtraj.to_json()
		# t4 = time()
		# print("Loaded nodes probtraj : %.2gs" % (t4-t3))

		observed_graph_json = None
		observed_nodes = [name for name, node in maboss_model.network.items() if in_observed_graph(node)]
		if len(observed_nodes) > 0 and server_host is None:
			# The simulation is still useful without it
			try:
				observed_graph_json = dumps(sparse_observed_graph(res.get_observed_graph(), observed_nodes))
			except Exception as e:
				observed_graph_json = dumps({'error': "Could not read the observed graph : " + str(e)})
		
		with transaction.atomic():
			maboss_simulation = MaBoSSSimulation.objects.get(id=maboss_simulation_id)
			maboss_simulation.fixpoints = fixed_points_json
			maboss_simulation.states_probtraj = states_probtraj_json
			maboss_simulation.nodes_probtraj = nodes_probtraj_json
			maboss_simulation.observed_graph = observed_graph_json

			maboss_simulation.status = MaBoSSSimulation.ENDED
			maboss_simulation.save()
			# print("Saved results : %.2gs" % (time()-t4))

	except Exception as e:
		
		with transaction.atomic():
			maboss_simulation = MaBoSSSimulation.objects.get(id=maboss_simulation_id)
			maboss_simulation.status = MaBoSSSimulation.ERROR
			maboss_simulation.error = str(e)
			maboss_simulation.save()
			print("Simulation failed ! : " + str(e))


class MaBoSSSimulationRemove(HasMaBoSSSimulation):

	def delete(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		self.simulation.delete()
		return Response(status=status.HTTP_200_OK)


class MaBossSettings(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		maboss_model = self.getMaBoSSModel()

		output_variables = {var: not value.is_internal for var, value in maboss_model.network.items()}
		observed_graph_nodes = {var: in_observed_graph(value) for var, value in maboss_model.network.items()}
		initial_states = maboss_model.network.get_istate()
		mutations = maboss_model.get_mutations()
		settings = {key: value for key, value in maboss_model.param.items() if not key.startswith("$")}

		if settings['use_physrandgen'] in [0, 1]:
			settings.update({'use_physrandgen': bool(settings['use_physrandgen'])})

		if settings['discrete_time'] in [0, 1]:
			settings.update({'discrete_time': bool(settings['discrete_time'])})

		return Response({
			'output_variables': OrderedDict(sorted(output_variables.items())),
			'observed_graph_nodes': OrderedDict(sorted(observed_graph_nodes.items())),
			'initial_states': dumpIstates(initial_states),
			'mutations': OrderedDict(sorted(mutations)),
			'settings': settings
		})


class MaBoSSSimulationBNDFile(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):
		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		bnd_filename = self.getBNDFilePath()

		if bnd_filename is None:
			return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

		return FileResponse(
			open(bnd_filename, 'rb'),
			as_attachment=True, filename=basename(bnd_filename)
		)


class MaBoSSSimulationCFGFile(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):
		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		cfg_filename = self.getCFGFilePath()

		if cfg_filename is None:
			return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

		return FileResponse(
			open(cfg_filename, 'rb'),
			as_attachment=True, filename=basename(cfg_filename)
		)


class MaBoSSSimulationNewModel(HasMaBoSSSimulation):

	# Creates a model, despite being a GET
	anonymous_methods = ()

	def get(self, request, project_id, simulation_id):
		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		try:
			new_model = LogicalModel(
				project=self.project,
				name=self.simulation.name + " model",
				bnd_file=File(open(self.getBNDFilePath(), 'rb'), name=basename(self.getBNDFilePath())),
				cfg_file=File(open(self.getCFGFilePath(), 'rb'), name=basename(self.getCFGFilePath())),
				format=LogicalModel.MABOSS
			)
			new_model.save()

			return Response(status=status.HTTP_200_OK)

		except:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MaBoSSSimulationStatusView(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):
		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		result = {
			'done': self.simulation.status == MaBoSSSimulation.ENDED,
			'failed': self.simulation.status in [MaBoSSSimulation.ERROR, MaBoSSSimulation.INTERRUPTED]
		}
		if self.simulation.status == MaBoSSSimulation.ERROR:
			result.update({'error': self.simulation.error})

		return Response(result, status=status.HTTP_200_OK)
