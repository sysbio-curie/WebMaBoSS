from api.views.HasProject import HasProject
from rest_framework.exceptions import NotFound, MethodNotAllowed, PermissionDenied
from django.conf import settings
from django.core.files.base import ContentFile
from api.models import LogicalModel
from os.path import join, splitext, basename

import maboss
import ginsim
import biolqm
import tempfile
import re
import json
from time import time
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

	def setName(self, name):
		
		self.model.name = name
		self.model.save()

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
			t0 = time()
			biolqm_model = biolqm.load(self.model.file.path)
			t1 = time()
			print("Loaded sbml with biolqm : %.2gs" % (t1-t0))
			maboss_model =biolqm.to_maboss(biolqm_model)
			print("Converted to MaBoSS : %.2gs" % (time()-t1))
			
			return maboss_model
			

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

	def getMinibnModel(self):

		if self.model.format == LogicalModel.MABOSS:
			maboss_sim = maboss.load(
				join(settings.MEDIA_ROOT, self.model.bnd_file.path),
				join(settings.MEDIA_ROOT, self.model.cfg_file.path)
			)
			return maboss.to_minibn(maboss_sim)
		elif self.model.format == LogicalModel.SBML:
			maboss_sim = maboss.loadSBML(join(settings.MEDIA_ROOT, self.model.file.path))
			return maboss.to_minibn(maboss_sim)
		elif self.model.format == LogicalModel.ZGINML:
			ginsim_model = ginsim.load(join(settings.MEDIA_ROOT, self.model.file.path))
			biolqm_model = ginsim.to_biolqm(ginsim_model)
			return biolqm.to_minibn(biolqm_model)
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
			biolqm_model = biolqm.load(join(settings.MEDIA_ROOT, self.model.file.path))
			for component in biolqm_model.getComponents():
				if component.getName() != "":
					
					component.setNodeID(re.sub('[^A-Za-z0-9_]+', '', component.getName()))
				
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
			ginsim_model = self.getBioLQMModel()

			path = tempfile.mkdtemp()
			tmp_sbml = tempfile.mkstemp(dir=path, suffix='.sbml')[1]

			biolqm.save(ginsim_model, tmp_sbml, "sbml")
			return tmp_sbml
			
		elif self.model.format == LogicalModel.SBML:
			return join(settings.MEDIA_ROOT, self.model.file.path)

		else:
			raise MethodNotAllowed()
			
	def getBNetModelFile(self):

		if self.model.format == LogicalModel.MABOSS:
			ginsim_model = self.getBioLQMModel()

			path = tempfile.mkdtemp()
			tmp_sbml = tempfile.mkstemp(dir=path, suffix='.bnet')[1]

			biolqm.save(ginsim_model, tmp_sbml, "bnet")
			return tmp_sbml
		
		else:
			raise MethodNotAllowed()

	def getZGINMLModelFile(self):

		if self.model.format == LogicalModel.ZGINML:
			return join(settings.MEDIA_ROOT, self.model.file.path)

		elif self.model.format == LogicalModel.MABOSS:
			ginsim_model = self.getBioLQMModel()

			path = tempfile.mkdtemp()
			tmp_zginml = tempfile.mkstemp(dir=path, suffix='.zginml')[1]
			biolqm.save(ginsim_model, tmp_zginml, "ginml")
			return tmp_zginml

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
			
	def getLayout(self):
		
		if self.model.layout_file:
			# print(self.model.layout_file)
			try:
				with open(self.model.layout_file.path, 'r') as layout_fd:
					layout = json.loads(layout_fd.read())
					# print(layout)
					return layout
			except:
				return None	
	def setLayout(self, layout):
		if self.model.layout_file:
			
			with open(self.model.layout_file.path, 'w') as layout_fd:
				layout_fd.write(json.dumps(layout))
		else:
			self.model.layout_file.save(basename(self.model.bnd_file.path), ContentFile(json.dumps(layout)))
			# print("Layout file created")
	
	def updateLayout(self, layout):
		if self.model.layout_file:
			with open(self.model.layout_file.path, 'w') as layout_fd:
				layout_fd.write(json.dumps(layout))
			