from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError

from django.db import connection
from threading import Thread
import tempfile

from api.models import ModelImport
from api.repositories import REPOSITORIES, RepositoryError
from api.views.HasUser import HasUser
from api.views.HasProject import HasProject
from api.views.logical_model.LogicalModels import convert_sbml, ginsim_to_maboss, check_maboss_model, remove_files, save_maboss_model


def get_repository(key):
	if key not in REPOSITORIES:
		raise NotFound
	return REPOSITORIES[key]


class RepositoryModels(HasUser):

	def get(self, request, repository):
		repository = get_repository(repository)
		try:
			return Response(repository.models())
		except RepositoryError as e:
			return Response(
				{'error': "Could not get the models of %s : %s" % (repository.title, e)},
				status=status.HTTP_502_BAD_GATEWAY
			)


class RepositoryImport(HasProject):

	def post(self, request, repository, project_id):
		HasProject.load(self, request, project_id)
		repository = get_repository(repository)

		try:
			model = repository.find(request.data.get('model_id'))
		except RepositoryError as e:
			return Response(
				{'error': "Could not get the models of %s : %s" % (repository.title, e)},
				status=status.HTTP_502_BAD_GATEWAY
			)
		if model is None:
			raise ValidationError("Unknown model of %s" % repository.title)

		model_import = ModelImport(
			project=self.project, repository=repository.key, remote_id=model['id'],
			name=request.data.get('name') or model['name'],
			use_sbml_names=str(request.data.get('use_sbml_names', 'true')).lower() == "true"
		)
		model_import.save()
		Thread(target=run_import, args=(model_import.id,)).start()

		return Response({'import_id': model_import.id})


class RepositoryImportStatus(HasProject):

	def get(self, request, project_id, import_id):
		HasProject.load(self, request, project_id)
		try:
			model_import = ModelImport.objects.get(id=import_id, project=self.project)
		except ModelImport.DoesNotExist:
			raise NotFound

		return Response({
			'done': model_import.status == ModelImport.ENDED,
			'failed': model_import.status == ModelImport.ERROR,
			'error': model_import.error,
			'model': model_import.model.id if model_import.model is not None else None,
		})


def import_model(model_import):
	""" Downloads the model, converts it to MaBoSS and saves it in the project """
	repository = REPOSITORIES[model_import.repository]
	model = repository.find(model_import.remote_id)

	with tempfile.TemporaryDirectory() as folder:
		path = repository.download(model, folder)

		if repository.format == "sbml":
			bnd_file, cfg_file, layout_file = convert_sbml(path, model_import.use_sbml_names)
		else:
			try:
				bnd_file, cfg_file = ginsim_to_maboss(path)
			except Exception as e:
				raise ValidationError("Error during conversion to MaBoSS : " + str(e))
			layout_file = None
			message = check_maboss_model(bnd_file, cfg_file)
			if len(message) > 0:
				remove_files(bnd_file, cfg_file)
				raise ValidationError("Conversion produced an invalid MaBoSS model : " + message[0])

	return save_maboss_model(model_import.project, model_import.name, bnd_file, cfg_file, layout_file)


def run_import(model_import_id):
	model_import = ModelImport.objects.get(id=model_import_id)
	try:
		model_import.model = import_model(model_import)
		model_import.status = ModelImport.ENDED

	except Exception as e:
		model_import.status = ModelImport.ERROR
		if isinstance(e, ValidationError):
			message = " ".join(str(detail) for detail in e.detail)
		elif isinstance(e, RepositoryError):
			message = "Could not download the model from %s : %s" % (REPOSITORIES[model_import.repository].title, e)
		else:
			message = "Could not import the model : %s" % e
		model_import.error = message
		print("Import failed ! : " + message)

	finally:
		model_import.save()
		# The thread's own connection to the database (not the one of a test, run in the same thread)
		if not connection.in_atomic_block:
			connection.close()
