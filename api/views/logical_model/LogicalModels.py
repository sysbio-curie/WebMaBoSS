from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound

from api.models import LogicalModel
from api.serializers import LogicalModelSerializer
from api.views.HasProject import HasProject

from urllib.request import urlretrieve
import os, tempfile, shutil, biolqm, re, maboss
from django.core.files import File
from django.core.files.storage import default_storage
import zipfile

def sbml_to_maboss(path, use_sbml_names=False):
	print("Converting %s to maboss" % path)
	# biolqm_model = biolqm.load(path)
	# for component in biolqm_model.getComponents():
	# 	if component.getName() != "":
			
	# 		component.setNodeID(re.sub('[^A-Za-z0-9_]+', '', component.getName()))
			
	# maboss_model = biolqm.to_maboss(biolqm_model)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	maboss.sbml_to_bnd_and_cfg(path, bnd_file[1], cfg_file[1], use_sbml_names)
	# maboss_model.print_bnd(open(bnd_file[1], 'w'))
	# maboss_model.print_cfg(open(cfg_file[1], 'w'))
	return (bnd_file[1], cfg_file[1])

def ginsim_to_maboss(path):
	print("Converting %s to maboss" % path)
	biolqm_model = biolqm.load(path)
	for component in biolqm_model.getComponents():
		if component.getName() != "":
			
			component.setNodeID(re.sub('[^A-Za-z0-9_]+', '', component.getName()))
			
	maboss_model = biolqm.to_maboss(biolqm_model)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	maboss_model.print_bnd(open(bnd_file[1], 'w'))
	maboss_model.print_cfg(open(cfg_file[1], 'w'))
	return (bnd_file[1], cfg_file[1])
	
def bnet_to_maboss(path):
	print("Converting bnet %s to maboss" % path)
	maboss_model = maboss.loadBNetCMaBoSS(path)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	maboss_model.print_bnd(open(bnd_file[1], 'w'))
	maboss_model.print_cfg(open(cfg_file[1], 'w'))
	return (bnd_file[1], cfg_file[1])
	
class LogicalModels(HasProject):

	def get(self, request, project_id, model_id=None):

		HasProject.load(self, request, project_id)

		try:
			if model_id is None:

				models = LogicalModel.objects.filter(
					project=self.project
				)
				serializer = LogicalModelSerializer(models, many=True)

				return Response(serializer.data)

			else:
				model = LogicalModel.objects.get(id=model_id)

				if model.project != self.project:
					raise PermissionDenied

				serializer = LogicalModelSerializer(model)

				return Response(serializer.data)

		except LogicalModel.DoesNotExist:
			raise NotFound


	def post(self, request, project_id):

		HasProject.load(self, request, project_id)
		
		# try:
		if 'url' in request.data.keys():
			print(request.data['url'])
			if request.data['url'].startswith("https://www.ebi.ac.uk"):
				zip_filename = tempfile.mkstemp(suffix=".zip")
				os.close(zip_filename[0])
				urlretrieve(request.data['url'], zip_filename[1])
				with zipfile.ZipFile(zip_filename[1],'r') as zip_file:
					
					temp_dir = tempfile.mkdtemp()
					zip_file.extract(zip_file.namelist()[0], temp_dir)
					(bnd_file, cfg_file) = sbml_to_maboss(
						os.path.join(temp_dir, zip_file.namelist()[0]), 
						request.data['use_sbml_names'].lower() == "true"
					)
					
					new_model = LogicalModel(
						project=self.project,
						name=request.data['name'],
						bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
						cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
						format=LogicalModel.MABOSS
					).save()
					os.remove(bnd_file)
					os.remove(cfg_file)
					shutil.rmtree(temp_dir)
				os.remove(zip_filename[1])
				
			else:
				
				sbml_file = tempfile.mkstemp(suffix=".sbml")
				os.close(sbml_file[0])
				urlretrieve(request.data['url'], sbml_file[1])
				(bnd_file, cfg_file) = sbml_to_maboss(
					sbml_file[1], 
					request.data['use_sbml_names'].lower() == "true"
				)
				
				new_model = LogicalModel(
					project=self.project,
					name=request.data['name'],
					bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
					cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
					format=LogicalModel.MABOSS
				).save()
				os.remove(bnd_file)
				os.remove(cfg_file)
				os.remove(sbml_file[1])
			
		elif 'file2' in request.data.keys():
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=request.data['file'],
				cfg_file=request.data['file2'],
				format=LogicalModel.MABOSS
			).save()

		elif request.data['file'].name.endswith(".zginml"):
			ginsim_file = tempfile.mkstemp(suffix=".zginml")
			with open(ginsim_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			bnd_file, cfg_file = ginsim_to_maboss(ginsim_file[1])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()
		
		elif request.data['file'].name.endswith(".bnet"):
			bnet_file = tempfile.mkstemp(suffix=".bnet")
			with open(bnet_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			bnd_file, cfg_file = bnet_to_maboss(bnet_file[1])
			print(bnd_file)
			print(cfg_file)
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()
			
		else:
			sbml_file = tempfile.mkstemp(suffix=".sbml")
			with open(sbml_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			bnd_file, cfg_file = ginsim_to_maboss(sbml_file[1])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()

		return Response(status=status.HTTP_200_OK)
		# except Exception as e:
		# 	return Response({'error': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)

	def delete(self, request, project_id, model_id):

		HasProject.load(self, request, project_id)

		try:
			model = LogicalModel.objects.get(id=model_id)

			if model.project != self.project:
				raise PermissionDenied

			model.delete()

		except LogicalModel.DoesNotExist:
			raise NotFound

		return Response(status=status.HTTP_200_OK)
