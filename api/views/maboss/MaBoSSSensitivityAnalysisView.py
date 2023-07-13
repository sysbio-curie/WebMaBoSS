from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed

from django.core.files import File
from django.conf import settings
from django.db import transaction
from api.views.HasModel import HasModel
from api.views.HasMaBoSSSensitivity import HasMaBoSSSensitivity
from api.models import LogicalModel, MaBoSSSimulation, MaBoSSSensitivitySimulation, MaBoSSSensitivityAnalysis
from api.serializers import MaBoSSSensitivityAnalysisSerializer
from threading import Thread
from os.path import join, exists, splitext, basename
from os import remove
from json import loads, dumps
from maboss import MaBoSSClient


class MaBoSSSensitivityAnalysisView(HasModel):

	def get(self, request, project_id, model_id):

		if request.user.is_anonymous:
			raise PermissionDenied
		
		HasModel.load(self, request, project_id, model_id)

		simulations = MaBoSSSensitivityAnalysis.objects.filter(model=self.model)
		serializer = MaBoSSSensitivityAnalysisSerializer(simulations, many=True)
		return Response(serializer.data)

	def post(self, request, project_id, model_id):

		if request.user.is_anonymous:
			raise PermissionDenied
			
		HasModel.load(self, request, project_id, model_id)

		maboss_model = self.getMaBoSSModel()		
		
		analysis_settings = loads(request.POST['settings'])
		candidate_variables = [candidate for candidate, value in analysis_settings['candidateVariables'].items() if value]
		
		for name, is_output in analysis_settings['outputVariables'].items():
			maboss_model.network[name].is_internal = not is_output

		nsimulations = 0
		if analysis_settings['singleMutations']['on']:
			nsimulations += len(candidate_variables)
			
		if analysis_settings['singleMutations']['off']:
			nsimulations += len(candidate_variables)
			
		if analysis_settings['doubleMutations']['on']:
			nsimulations += len(candidate_variables) * (len(candidate_variables)-1)
			
		if analysis_settings['doubleMutations']['off']:
			nsimulations += len(candidate_variables) * (len(candidate_variables)-1)
			
		if analysis_settings['doubleMutations']['on'] and analysis_settings['doubleMutations']['off']:
			nsimulations += 2*(len(candidate_variables) * (len(candidate_variables)-1))
			
		if nsimulations > 1000:
			return Response({'analysis_id': -1, 'error': "too_much_simulations"}, status=status.HTTP_200_OK)

		if self.model.format == LogicalModel.ZGINML:

			bnd_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".bnd")
			bnd_file = open(bnd_path, 'w')
			maboss_model.print_bnd(out=bnd_file)
			bnd_file.close()

			cfg_path = join(settings.TMP_ROOT, splitext(basename(self.model.file.path))[0] + ".cfg")
			cfg_file = open(cfg_path, 'w')
			maboss_model.print_cfg(out=cfg_file)
			cfg_file.close()

			sensitivity_analysis = MaBoSSSensitivityAnalysis(
				project=self.project,
				model=self.model,
				name=analysis_settings['name'],
				bnd_file=File(open(bnd_path, 'rb'), name=basename(bnd_path)),
				cfg_file=File(open(cfg_path, 'rb'), name=basename(cfg_path)),
				nsimulations = nsimulations
			)
			sensitivity_analysis.save()

			remove(bnd_path)
			remove(cfg_path)

		elif self.model.format == LogicalModel.MABOSS:

			sensitivity_analysis = MaBoSSSensitivityAnalysis(
				project=self.project,
				model=self.model,
				name=analysis_settings['name'],
				bnd_file=File(open(join(settings.MEDIA_ROOT, self.model.bnd_file.path), 'rb'), name=basename(self.model.bnd_file.path)),
				cfg_file=File(open(join(settings.MEDIA_ROOT, self.model.cfg_file.path), 'rb'), name=basename(self.model.cfg_file.path)),
				nsimulations=nsimulations
			)
			sensitivity_analysis.save()

		else:
			return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

		maboss_model.param['thread_count'] = 6
		maboss_model.param['time_tick'] = float(maboss_model.param['max_time'])/10

		thread = Thread(target=run_analysis, args=(maboss_model, sensitivity_analysis, analysis_settings, candidate_variables))
		thread.start()

		return Response({'analysis_id': sensitivity_analysis.id}, status=status.HTTP_200_OK)

class MaBoSSSensitivityAnalysisRemove(HasMaBoSSSensitivity):

	def delete(self, request, project_id, analysis_id):

		HasMaBoSSSensitivity.load(self, request, project_id, analysis_id)

		self.analysis.delete()
		return Response(status=status.HTTP_200_OK)

def run_analysis(maboss_model, sensitivity_analysis, analysis_settings, candidate_variables):

	server_host = analysis_settings.get('serverHost')
	server_port = analysis_settings.get('serverPort')

	if analysis_settings['singleMutations']['on']:

		for species in candidate_variables:
			maboss_simulation = MaBoSSSensitivitySimulation(
				sensitivity_analysis=sensitivity_analysis,
				name=("%s++" % species),
			)
			maboss_simulation.save()

			t_model = maboss_model.copy()
			t_model.mutate(species, 'ON')

			# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
			# thread.start()
			run_simulation(t_model, maboss_simulation.id, server_host, server_port)

	if analysis_settings['singleMutations']['off']:

		for species in candidate_variables:
			maboss_simulation = MaBoSSSensitivitySimulation(
				sensitivity_analysis=sensitivity_analysis,
				name=("%s--" % species),
			)
			maboss_simulation.save()

			t_model = maboss_model.copy()
			t_model.mutate(species, 'OFF')

			# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
			# thread.start()
			run_simulation(t_model, maboss_simulation.id, server_host, server_port)


	if analysis_settings['doubleMutations']['on']:

		for species in candidate_variables:
			for subspecies in candidate_variables:
				if subspecies != species:
					maboss_simulation = MaBoSSSensitivitySimulation(
						sensitivity_analysis=sensitivity_analysis,
						name=("%s++, %s++" % (species, subspecies)),
						status=MaBoSSSensitivitySimulation.BUSY
					)
					maboss_simulation.save()

					t_model = maboss_model.copy()
					t_model.mutate(species, 'ON')
					t_model.mutate(subspecies, 'ON')

					# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
					# thread.start()
					run_simulation(t_model, maboss_simulation.id, server_host, server_port)


			if analysis_settings['doubleMutations']['off']:

				for subspecies in candidate_variables:
					if subspecies != species:
						maboss_simulation = MaBoSSSensitivitySimulation(
							sensitivity_analysis=sensitivity_analysis,
							name=("%s++, %s--" % (species, subspecies)),
							status=MaBoSSSensitivitySimulation.BUSY
						)
						maboss_simulation.save()

						t_model = maboss_model.copy()
						t_model.mutate(species, 'ON')
						t_model.mutate(subspecies, 'OFF')

						# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
						# thread.start()
						run_simulation(t_model, maboss_simulation.id, server_host, server_port)


	if analysis_settings['doubleMutations']['off']:

		for species in candidate_variables:
			for subspecies in candidate_variables:
				if subspecies != species:
					maboss_simulation = MaBoSSSensitivitySimulation(
						sensitivity_analysis=sensitivity_analysis,
						name=("%s--, %s--" % (species, subspecies)),
						status=MaBoSSSensitivitySimulation.BUSY
					)
					maboss_simulation.save()

					t_model = maboss_model.copy()
					t_model.mutate(species, 'OFF')
					t_model.mutate(subspecies, 'OFF')

					# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
					# thread.start()
					run_simulation(t_model, maboss_simulation.id, server_host, server_port)


			if analysis_settings['doubleMutations']['on']:

				for subspecies in candidate_variables:
					if subspecies != species:
						maboss_simulation = MaBoSSSensitivitySimulation(
							sensitivity_analysis=sensitivity_analysis,
							name=("%s--, %s++" % (species, subspecies)),
							status=MaBoSSSensitivitySimulation.BUSY
						)
						maboss_simulation.save()

						t_model = maboss_model.copy()
						t_model.mutate(species, 'OFF')
						t_model.mutate(subspecies, 'ON')

						# thread = Thread(target=run_simulation, args=(t_model, maboss_simulation.id, server_host, server_port))
						# thread.start()
						run_simulation(t_model, maboss_simulation.id, server_host, server_port)


def run_simulation(maboss_model, maboss_simulation_id, server_host, server_port):

	try:
		if server_host is not None and server_port is not None:
			mbcli = MaBoSSClient(server_host, int(server_port))
			res = mbcli.run(maboss_model)
		else:
			res = maboss_model.run()

		fixed_points = res.get_fptable()
		if fixed_points is not None:
			fixed_points_json = fixed_points.to_json()
		else:
			fixed_points_json = "{}"

		states_probtraj = res.get_states_probtraj()
		states_probtraj_json = states_probtraj.to_json()

		# nodes_probtraj = res.get_nodes_probtraj()
		# nodes_probtraj_json = nodes_probtraj.to_json()

		with transaction.atomic():
			maboss_simulation = MaBoSSSensitivitySimulation.objects.get(id=maboss_simulation_id)
			maboss_simulation.fixpoints = fixed_points_json
			maboss_simulation.states_probtraj = states_probtraj_json
			# maboss_simulation.nodes_probtraj = nodes_probtraj_json
			maboss_simulation.status = MaBoSSSensitivitySimulation.ENDED
			maboss_simulation.save()
			
	except:
		with transaction.atomic():
			maboss_simulation = MaBoSSSensitivitySimulation.objects.get(id=maboss_simulation_id)
			maboss_simulation.status = MaBoSSSensitivitySimulation.ERROR
			maboss_simulation.error = "Simulation failed"
			maboss_simulation.save()

class MaBoSSSensitivitySteadyStatesView(HasMaBoSSSensitivity):

	def get(self, request, project_id, analysis_id):

		HasMaBoSSSensitivity.load(self, request, project_id, analysis_id)

		results = {}
		simulations = MaBoSSSensitivitySimulation.objects.filter(sensitivity_analysis=self.analysis)

		results.update({'results': {}})

		for simulation in simulations:

			fixed_points = None

			if simulation.states_probtraj is not None:
				fixed_points = {}
				for key, values in loads(simulation.states_probtraj).items():
					last_time = list(values.keys())[len(values.keys()) - 1]
					if values[last_time] > 0:
						fixed_points.update({key: values[last_time]})

			results['results'].update({simulation.name: fixed_points})

		return Response(results, status=status.HTTP_200_OK)


class MaBoSSSensitivityStatusView(HasMaBoSSSensitivity):

	def get(self, request, project_id, analysis_id):

		HasMaBoSSSensitivity.load(self, request, project_id, analysis_id)

		simulations = MaBoSSSensitivitySimulation.objects.filter(sensitivity_analysis=self.analysis)
		finished = [simulation.status == MaBoSSSensitivitySimulation.ENDED for simulation in simulations]
		failed = [simulation.status in [MaBoSSSensitivitySimulation.ERROR, MaBoSSSensitivityAnalysis.INTERRUPTED] for simulation in simulations]
		result = {
			'done': float(sum(finished))/float(self.analysis.nsimulations) if len(simulations) > 0 else 0,
			'failed': sum(failed) > 0
		}
		
		return Response(result, status=status.HTTP_200_OK)
