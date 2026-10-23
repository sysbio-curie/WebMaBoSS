from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from api.models import LogicalModel
from api.serializers import LogicalModelSerializer
from api.views.HasProject import HasProject
from api.views.commons.parseLayout import parseLayout
import os, tempfile, shutil, biolqm, re, maboss, json
from django.core.files import File
from django.core.files.storage import default_storage
from rest_framework import authentication, permissions
def sbml_to_maboss(path, use_sbml_names=False):
	print("Converting %s to maboss" % path)
	# biolqm_model = biolqm.load(path)
	# for component in biolqm_model.getComponents():
	# 	if component.getName() != "":
			
	# 		component.setNodeID(re.sub('[^A-Za-z0-9_]+', '', component.getName()))
			
	# maboss_model = biolqm.to_maboss(biolqm_model)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	layout_file = tempfile.mkstemp(suffix=".json")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	os.close(layout_file[0])
	maboss.sbml_to_bnd_and_cfg(path, bnd_file[1], cfg_file[1], use_sbml_names)
	
	layout = parseLayout(path)
	if layout is None:
		return (bnd_file[1], cfg_file[1], None)
	else:
		with open(layout_file[1], "w") as layout_fd:
			layout_fd.write(json.dumps(layout))
		
		return (bnd_file[1], cfg_file[1], layout_file[1])

def biolqm_to_maboss(biolqm_model, use_names=True):
	""" Writes a bioLQM model as MaBoSS files, with the names of its components when they can be identifiers """
	if use_names:
		components = biolqm_model.getComponents()
		# The name without what an identifier can't have, unless it still isn't one (like 14-3-3)
		names = [re.sub('[^A-Za-z0-9_]+', '', component.getName()) for component in components]
		ids = [
			name if re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', name) else component.getNodeID()
			for name, component in zip(names, components)
		]
		# Two components can have the same name
		if len(set(ids)) == len(ids):
			for component, new_id in zip(components, ids):
				component.setNodeID(new_id)

	maboss_model = biolqm.to_maboss(biolqm_model)

	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	with open(bnd_file[1], 'w') as bnd:
		maboss_model.print_bnd(bnd)
	with open(cfg_file[1], 'w') as cfg:
		maboss_model.print_cfg(cfg)
	return (bnd_file[1], cfg_file[1])

def ginsim_to_maboss(path):
	print("Converting %s to maboss" % path)
	return biolqm_to_maboss(biolqm.load(path))

def remove_files(*paths):
	for path in paths:
		if path is not None and os.path.exists(path):
			os.remove(path)

def convert_sbml(path, use_sbml_names):
	"""
	Converts an SBML-qual model to MaBoSS files (bnd, cfg, layout or None), which are checked. MaBoSS converts it, with
	the names of the species if asked, or their ids if two have the same name. Otherwise bioLQM, which reads more of
	SBML-qual (multivalued species, comparisons).
	"""
	errors = []
	for use_names in ([True, False] if use_sbml_names else [False]):
		try:
			bnd_file, cfg_file, layout_file = sbml_to_maboss(path, use_names)
		except Exception as e:
			errors.append(str(e))
			continue
		message = check_maboss_model(bnd_file, cfg_file)
		if len(message) == 0:
			return bnd_file, cfg_file, layout_file
		errors.append(message[0])
		remove_files(bnd_file, cfg_file, layout_file)

	# Not for the models MaBoSS can't simulate anyway
	if not any("nodes are not compatible" in error for error in errors):
		try:
			bnd_file, cfg_file = biolqm_to_maboss(biolqm.load(path, "sbml"), use_sbml_names)
			message = check_maboss_model(bnd_file, cfg_file)
			if len(message) == 0:
				layout = parseLayout(path)
				if layout is None:
					return bnd_file, cfg_file, None
				layout_file = tempfile.mkstemp(suffix=".json")
				os.close(layout_file[0])
				with open(layout_file[1], "w") as layout_fd:
					layout_fd.write(json.dumps(layout))
				return bnd_file, cfg_file, layout_file[1]
			remove_files(bnd_file, cfg_file)
		except Exception:
			pass

	raise ValidationError("Error during conversion to MaBoSS : " + errors[0])

def save_maboss_model(project, name, bnd_file, cfg_file, layout_file=None):
	""" Saves converted MaBoSS files as a model of the project, and removes them """
	model = LogicalModel(
		project=project,
		name=name,
		bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
		cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
		layout_file=File(open(layout_file, 'rb'), name=os.path.basename(layout_file)) if layout_file is not None else None,
		format=LogicalModel.MABOSS
	)
	model.save()
	remove_files(bnd_file, cfg_file, layout_file)
	return model
	
def bnet_to_maboss(path):
	print("Converting bnet %s to maboss" % path)
	maboss_model = maboss.loadBNet(path)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	maboss_model.print_bnd(open(bnd_file[1], 'w'))
	maboss_model.print_cfg(open(cfg_file[1], 'w'))
	return (bnd_file[1], cfg_file[1])
	
def tabularqual_to_maboss(path):
	print("Converting tabularqual %s to maboss" % path)
	maboss_model = maboss.loadTabularQual(path)
	
	bnd_file = tempfile.mkstemp(suffix=".bnd")
	cfg_file = tempfile.mkstemp(suffix=".cfg")
	os.close(bnd_file[0])
	os.close(cfg_file[0])
	maboss_model.print_bnd(open(bnd_file[1], 'w'))
	maboss_model.print_cfg(open(cfg_file[1], 'w'))
	return (bnd_file[1], cfg_file[1])

def check_maboss_model(bnd_file, cfg_file):

	message = []
	try:
		sim = maboss.load(bnd_file, cfg_file, cmaboss=True)
		sim.check()
	except Exception as e:
		return [str(e)]
	
	return message
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

		# The format is given by the extension, in lowercase : model.ZGINML is a GINsim model
		extension = os.path.splitext(request.data['file'].name)[1].lower() if 'file' in request.data.keys() else None

		if 'file2' in request.data.keys():
			
			tmp_bnd_path = tempfile.mkstemp(suffix=".bnd")
			tmp_cfg_path = tempfile.mkstemp(suffix=".cfg")
			
			with open(tmp_bnd_path[1], 'wb') as f:
				f.write(request.data['file'].read())
			with open(tmp_cfg_path[1], 'wb') as f:
				f.write(request.data['file2'].read())
	
			message = check_maboss_model(tmp_bnd_path[1], tmp_cfg_path[1])
			
			if len(message) > 0:
				raise ValidationError("Invalid MaBoSS model : " + message[0])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=request.data['file'],
				cfg_file=request.data['file2'],
				format=LogicalModel.MABOSS
			).save()	
	
			os.remove(tmp_bnd_path[1])
			os.remove(tmp_cfg_path[1])

		elif extension == ".zginml":
			ginsim_file = tempfile.mkstemp(suffix=".zginml")
			with open(ginsim_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			try:
				bnd_file, cfg_file = ginsim_to_maboss(ginsim_file[1])
			except Exception as e:
				raise ValidationError("Error during conversion to MaBoSS : " + str(e))
		
			message = check_maboss_model(bnd_file, cfg_file)
			
			if len(message) > 0:
				raise ValidationError("Conversion produced an invalid MaBoSS model : " + message[0])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()
			
			os.remove(ginsim_file[1])
			os.remove(bnd_file)
			os.remove(cfg_file)
		
		elif extension == ".bnet":
			bnet_file = tempfile.mkstemp(suffix=".bnet")
			with open(bnet_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			try:
				bnd_file, cfg_file = bnet_to_maboss(bnet_file[1])
			except Exception as e:
				raise ValidationError("Error during conversion to MaBoSS : " + str(e))
					
			message = check_maboss_model(bnd_file, cfg_file)
			
			if len(message) > 0:
				raise ValidationError("Conversion produced an invalid MaBoSS model : " + message[0])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()
			
			os.remove(bnet_file[1])
			os.remove(bnd_file)
			os.remove(cfg_file)
			
		elif extension == ".xlsx":
			tabularqual_file = tempfile.mkstemp(suffix=".xlsx")
			with open(tabularqual_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			try:
				bnd_file, cfg_file = tabularqual_to_maboss(tabularqual_file[1])
			except Exception as e:
				raise ValidationError("Error during conversion to MaBoSS : " + str(e))
					
			message = check_maboss_model(bnd_file, cfg_file)
			
			if len(message) > 0:
				raise ValidationError("Conversion produced an invalid MaBoSS model : " + message[0])
			
			LogicalModel(
				project=self.project,
				name=request.data['name'],
				bnd_file=File(open(bnd_file, 'rb'), name=os.path.basename(bnd_file)),
				cfg_file=File(open(cfg_file, 'rb'), name=os.path.basename(cfg_file)),
				format=LogicalModel.MABOSS			
			).save()
			
			os.remove(tabularqual_file[1])
			os.remove(bnd_file)
			os.remove(cfg_file)
			
		else:
			sbml_file = tempfile.mkstemp(suffix=".sbml")
			with open(sbml_file[0], 'wb') as f:				
				f.write(request.data['file'].read())

			try:
				bnd_file, cfg_file, layout_file = convert_sbml(
					sbml_file[1], request.data['use_sbml_names'].lower() == "true"
				)
			finally:
				os.remove(sbml_file[1])

			save_maboss_model(self.project, request.data['name'], bnd_file, cfg_file, layout_file)

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
