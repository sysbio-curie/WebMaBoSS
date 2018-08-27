from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.conf import settings
# from django.core.serializers.json import DjangoJSONEncoder

from api.models import LogicalModel, MaBoSSSimulation

from threading import Thread
from os.path import join
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

class LogicalModelSimulation(APIView):

	def post(self, request, pk):
		try:

			model = LogicalModel.objects.get(pk=pk)
			import ginsim
			path = join(settings.MEDIA_ROOT, model.file.path)
			ginsim_model = ginsim.load(path)
			maboss_model = ginsim.to_maboss(ginsim_model)

			maboss_simulation = MaBoSSSimulation()
			maboss_simulation.save()

			maboss_model.update_parameters(
				sample_count=int(request.POST['sampleCount']),
				max_time=float(request.POST['maxTime']),
				time_tick=float(request.POST['timeTick'])
			)

			thread = Thread(target=run_simulation, args=(maboss_model, maboss_simulation.id))
			thread.start()

			return Response({'simulation_id': maboss_simulation.id}, status=status.HTTP_200_OK)


		except LogicalModel.DoesNotExist:
			raise Http404


from django.db import transaction
import json

def run_simulation(maboss_model, maboss_simulation_id):

	try:
		maboss_simulation = MaBoSSSimulation.objects.get(id=maboss_simulation_id)

		with transaction.atomic():
			maboss_simulation.status = MaBoSSSimulation.BUSY
			maboss_simulation.save()

		res = maboss_model.run()

		fixed_points = res.get_fptable()
		print("get_fptable done")
		fixed_points_json = fixed_points.to_json()
		print("to json done")

		with transaction.atomic():
			maboss_simulation.fixpoints = fixed_points_json
			maboss_simulation.status = MaBoSSSimulation.ENDED
			maboss_simulation.save()

		states_probtraj = res.get_states_probtraj()
		print("get_states_probtraj done")
		states_probtraj_json = states_probtraj.to_json()
		print("to json done")

		with transaction.atomic():
			maboss_simulation.states_probtraj = states_probtraj_json
			maboss_simulation.save()

		nodes_probtraj = res.get_nodes_probtraj()
		print("get_nodes_probtraj done")
		nodes_probtraj_json = nodes_probtraj.to_json()
		print("to json done")

		with transaction.atomic():
			maboss_simulation.nodes_probtraj = nodes_probtraj_json
			maboss_simulation.save()


	except:
		with transaction.atomic():
			maboss_simulation.status = MaBoSSSimulation.ERROR
			maboss_simulation.error = "Simulation failed"


class MaBoSSResultsFixedPoints(APIView):

	def get(self, request, pk):

		try:
			simulation = MaBoSSSimulation.objects.get(id=int(pk))
			if simulation.fixpoints is not None:
				fixed_points = json.loads(simulation.fixpoints)
			else:
				fixed_points = None

			return Response(
					{
						'fixed_points': fixed_points,
					},
					status=status.HTTP_200_OK
				)

		except:
			raise Http404

class MaBoSSResultsStatesProbTraj(APIView):

	def get(self, request, pk):

		try:
			simulation = MaBoSSSimulation.objects.get(id=int(pk))
			if simulation.states_probtraj is not None:
				states_probtraj = json.loads(simulation.states_probtraj)
			else:
				states_probtraj = None

			return Response(
				{
					'states_probtraj': states_probtraj,
				},
				status=status.HTTP_200_OK
			)

		except:
			raise Http404

class MaBoSSResultsNodesProbTraj(APIView):

	def get(self, request, pk):

		try:
			simulation = MaBoSSSimulation.objects.get(id=int(pk))
			if simulation.nodes_probtraj is not None:
				nodes_probtraj = json.loads(simulation.nodes_probtraj)
			else:
				nodes_probtraj = None

			return Response(
				{
					'nodes_probtraj': nodes_probtraj,
				},
				status=status.HTTP_200_OK
			)

		except:
			raise Http404

