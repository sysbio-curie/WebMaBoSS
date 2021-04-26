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

		elif self.model.format == LogicalModel.SBML:
			biolqm_model = biolqm.load(self.model.file.path)
			return biolqm.to_maboss(biolqm_model)

		else:
			raise MethodNotAllowed()

	def saveMaBoSSModel(self, maboss_sim):

		if self.model.format == LogicalModel.MABOSS:
			maboss_sim.print_bnd(out=open(join(settings.MEDIA_ROOT, self.model.bnd_file.path), 'w'))
			maboss_sim.print_cfg(out=open(join(settings.MEDIA_ROOT, self.model.cfg_file.path), 'w'))

	def getBioLQMModel(self):

		if self.model.format == LogicalModel.MABOSS:
			maboss_sim = maboss.load(
				join(settings.MEDIA_ROOT, self.model.bnd_file.path),
				join(settings.MEDIA_ROOT, self.model.cfg_file.path)
			)
			biolqm_model = maboss.to_biolqm(maboss_sim)
			return biolqm_model
			
		elif self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))
			return ginsim.to_biolqm(ginsim_model)

		elif self.model.format == LogicalModel.SBML:
			biolqm_model = biolqm.load(join(settings.MEDIA_ROOT, self.model.file.path))
			return biolqm_model

		else:
			raise MethodNotAllowed()

	def getGINSimModel(self):

		if self.model.format == LogicalModel.ZGINML:
			return ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))

		elif self.model.format == LogicalModel.MABOSS:
			biolqm_model = self.getBioLQMModel()
			ginsim_model = biolqm.to_ginsim(biolqm_model)
			ginsim.service("layout").runLayout(2, ginsim_model)
			return ginsim_model
			
		elif self.model.format == LogicalModel.SBML:
			print(join(settings.MEDIA_ROOT, self.model.file.path))
			biolqm_model = biolqm.load(join(settings.MEDIA_ROOT, self.model.file.path))
			for component in biolqm_model.getComponents():
				component.setNodeID(component.getName().replace("/", "_"))
			ginsim_model = biolqm.to_ginsim(biolqm_model)
			ginsim.service("layout").runLayout(2, ginsim_model)
			return ginsim_model
			
		else:
			raise MethodNowAllowed()

		
	def getSBMLModelFile(self):

		if self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))

			path = tempfile.mkdtemp()
			tmp_sbml = tempfile.mkstemp(dir=path, suffix='.sbml')[1]

			biolqm.save(ginsim_model, tmp_sbml, "sbml")
			return tmp_sbml

		elif self.model.format == LogicalModel.MABOSS:
			ginsim_model = self.getGINSimModel()

			path = tempfile.mkdtemp()
			tmp_sbml = tempfile.mkstemp(dir=path, suffix='.sbml')[1]

			biolqm.save(ginsim_model, tmp_sbml, "sbml")
			return tmp_sbml
			
		elif self.model.format == LogicalModel.SBML:
			return join(settings.MEDIA_ROOT, self.model.file.path)

		else:
			raise MethodNotAllowed()

	def getZGINMLModelFile(self):

		if self.model.format == LogicalModel.ZGINML:
			return join(settings.MEDIA_ROOT, self.model.file.path)

		elif self.model.format == LogicalModel.MABOSS:
			ginsim_model = self.getGINSimModel()

			path = tempfile.mkdtemp()
			tmp_zginml = tempfile.mkstemp(dir=path, suffix='.zginml')[1]
			biolqm.save(ginsim_model)

	def getMaBoSSBNDFile(self):

		if self.model.format == LogicalModel.MABOSS:
			return join(settings.MEDIA_ROOT, self.model.bnd_file.path)

		elif self.model.format == LogicalModel.ZGINML:
			path = tempfile.mkdtemp()
			tmp_bnd = tempfile.mkstemp(dir=path, suffix='.bnd')[1]
			maboss_model = self.getMaBoSSModel()

			with open(tmp_bnd, 'w') as file:
				maboss_model.print_bnd(out=file)

			return tmp_bnd

	def getMaBoSSCFGFile(self):

		if self.model.format == LogicalModel.MABOSS:
			return join(settings.MEDIA_ROOT, self.model.cfg_file.path)

		elif self.model.format == LogicalModel.ZGINML:
			path = tempfile.mkdtemp()
			tmp_cfg = tempfile.mkstemp(dir=path, suffix='.cfg')[1]
			maboss_model = self.getMaBoSSModel()

			with open(tmp_cfg, 'w') as file:
				maboss_model.print_cfg(out=file)

			return tmp_cfg