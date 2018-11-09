from rest_framework.response import Response
from rest_framework import status

from django.http import HttpResponse, FileResponse
from django.conf import settings

from api.views.HasModel import HasModel
from api.serializers import LogicalModelNameSerializer

from os.path import join, basename

import ginsim
from json import loads
import tempfile


class LogicalModelFile(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		return FileResponse(
			open(join(settings.MEDIA_ROOT, self.model.file.path), 'rb'),
			as_attachment=True, filename=basename(self.model.file.path)
		)


class LogicalModelSBMLFile(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		sbml_filename = self.getSBMLModelFile()

		return FileResponse(
			open(sbml_filename, 'rb'),
			as_attachment=True, filename=basename(sbml_filename)
		)


class LogicalModelName(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		serializer = LogicalModelNameSerializer(self.model)

		return Response(serializer.data)


class LogicalModelNodes(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)
		maboss_model = self.getMaBoSSModel()

		return Response(list(maboss_model.network.keys()))


class LogicalModelGraph(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		ginsim_model = self.getGINSimModel()
		fig = ginsim.get_image(ginsim_model)

		return HttpResponse(fig, content_type="image/png")


	def post(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)

		steady_state = loads(request.data['steady_state'])
		ginsim_model = self.getGINSimModel()
		fig = ginsim.get_image(ginsim_model, steady_state)

		return HttpResponse(fig, content_type="image/png")


class LogicalModelGraphRaw(HasModel):

	def get(self, request, project_id, model_id):

		HasModel.load(self, request, project_id, model_id)
		ginsim_model = self.getGINSimModel()

		# from ginsim.gateway import japi
		# This won't work in parallel... but that's ok for now

		path = tempfile.mkdtemp()
		tmp_reggraph = tempfile.mkstemp(dir=path, suffix='.reg')[1]

		ginsim.gateway.japi.gs.service("reggraph").export(ginsim_model, tmp_reggraph)

		edges = []
		nodes = []
		with open(tmp_reggraph, 'r') as reggraph:
			for line in reggraph.readlines():
				(a, sign, b) = line.strip().split()
				nodes.append(a)
				nodes.append(b)
				edges.append((a, b, (1 if sign == "->" else 0)))

		nodes = list(set(nodes))

		return Response(
			{
				'nodes': nodes,
				'edges': edges
			},
			status=status.HTTP_200_OK
		)
