from api.views.HasProject import HasProject
from rest_framework.exceptions import NotFound, MethodNotAllowed, PermissionDenied
from django.conf import settings

from api.models import LogicalModel
from os.path import join, splitext, basename

import maboss
import ginsim
import biolqm
import tempfile


class HasModel(HasProject):

	def __init__(self, *args, **kwargs):
		HasProject.__init__(self, *args, **kwargs)
		self.model = None

	def load(self, request, project_id, model_id):

		HasProject.load(self, request, project_id)

		try:
			model = LogicalModel.objects.get(id=model_id)
			if model.project != self.project:
				raise PermissionDenied

			self.model = model

		except LogicalModel.DoesNotExist:
			raise NotFound

	def getMaBoSSModel(self):

		if self.model.format == LogicalModel.MABOSS:
			return maboss.load(
				join(settings.MEDIA_ROOT, self.model.bnd_file.path),
				join(settings.MEDIA_ROOT, self.model.cfg_file.path)
			)

		elif self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(self.model.file.path)
			return ginsim.to_maboss(ginsim_model)

		else:
			raise MethodNotAllowed

	def getBioLQMModel(self):

		if self.model.format == LogicalModel.MABOSS:
			maboss_sim = maboss.load(
				join(settings.MEDIA_ROOT, self.model.bnd_file.path),
				join(settings.MEDIA_ROOT, self.model.cfg_file.path)
			)

			path = tempfile.mkdtemp()
			tmp_bnet = tempfile.mkstemp(dir=path, suffix='.bnet')[1]

			with open(tmp_bnet, "w") as bnet_file:
				maboss_sim.print_logical_rules(bnet_file)

			f = open(tmp_bnet, "r")
			string = f.readlines()
			new_string = [line.replace(" : ", ", ") for line in string]
			f.close()

			f = open(tmp_bnet, "w")
			f.write("targets, factors\n")
			f.writelines(new_string)
			f.close()
			return biolqm.load(tmp_bnet)

		elif self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))
			return ginsim.to_biolqm(ginsim_model)

		else:
			raise MethodNotAllowed

	def getGINSimModel(self):

		if self.model.format == LogicalModel.ZGINML:
			return ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))

		elif self.model.format == LogicalModel.MABOSS:
			biolqm_model = self.getBioLQMModel()
			ginsim_model = biolqm.to_ginsim(biolqm_model)
			ginsim.layout(ginsim_model, 2)
			return ginsim_model

		else:
			raise MethodNotAllowed

	def getSBMLModelFile(self):

		if self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))

			path = tempfile.mkdtemp()
			tmp_sbml = tempfile.mkstemp(dir=path, suffix='.sbml')[1]

			ginsim.to_sbmlqual(ginsim_model, tmp_sbml)

			return tmp_sbml
