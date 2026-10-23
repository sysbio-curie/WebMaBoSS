from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.core.files import File

from api.models.project import Project, add_default_project
from django.contrib.auth.models import User

from random import choice
from string import ascii_uppercase, ascii_lowercase, digits
from os.path import join, exists, basename, dirname, isdir
from shutil import rmtree

def new_model_path(project):
	rand_string = ''.join(choice(ascii_uppercase + ascii_lowercase + digits) for _ in range(12))
	while isdir(join(settings.MEDIA_ROOT, project.path, rand_string)):
		rand_string = ''.join(choice(ascii_uppercase + ascii_lowercase + digits) for _ in range(12))

	return rand_string

def path_logical_model(instance, filename):
	return join(instance.project.path, 'logical_models', instance.path, basename(filename))

def remove_logical_model(sender, instance, **kwargs):
	if instance.format == LogicalModel.ZGINML and instance.file and exists(join(settings.MEDIA_ROOT, instance.file.path)):
		rmtree(dirname(join(settings.MEDIA_ROOT, instance.file.path)))
	elif instance.format == LogicalModel.MABOSS:
		if instance.bnd_file and exists(join(settings.MEDIA_ROOT, instance.bnd_file.path)):
			rmtree(dirname(join(settings.MEDIA_ROOT, instance.bnd_file.path)))
		if instance.cfg_file and exists(join(settings.MEDIA_ROOT, instance.cfg_file.path)):
			rmtree(dirname(join(settings.MEDIA_ROOT, instance.cfg_file.path)))

class LogicalModel(models.Model):

	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	name = models.CharField(max_length=256)
	path = models.CharField(max_length=12)

	ZGINML = 'ZGinML'
	MABOSS = 'MaBoSS'
	SBML = 'SBML'

	FORMATS = (
		(ZGINML, 'ZGinML'),
		(MABOSS, 'MaBoSS'),
		(SBML, 'SBML')
	)

	format = models.CharField(max_length=10, choices=FORMATS, default=ZGINML)

	file = models.FileField(upload_to=path_logical_model, blank=True)

	bnd_file = models.FileField(upload_to=path_logical_model, blank=True)
	cfg_file = models.FileField(upload_to=path_logical_model, blank=True)

	layout_file = models.FileField(upload_to=path_logical_model, blank=True)

	def save(self, *args, **kwargs):

		if self.project:
			self.path = new_model_path(self.project)
			super(LogicalModel, self).save(*args, **kwargs)
			
pre_delete.connect(remove_logical_model, sender=LogicalModel)


def path_tagged_logical_model(instance, filename):
	return join(instance.model.project.path, 'logical_models', instance.model.path, instance.tag, basename(filename))

def remove_tagged_logical_model(sender, instance, **kwargs):
	if instance.model.format == LogicalModel.ZGINML and exists(join(settings.MEDIA_ROOT, instance.file.path)):
		rmtree(dirname(join(settings.MEDIA_ROOT, instance.file.path)))
	elif instance.model.format == LogicalModel.MABOSS:
		if exists(join(settings.MEDIA_ROOT, instance.bnd_file.path)):
			rmtree(dirname(join(settings.MEDIA_ROOT, instance.bnd_file.path)))
		if exists(join(settings.MEDIA_ROOT, instance.cfg_file.path)):
			rmtree(dirname(join(settings.MEDIA_ROOT, instance.cfg_file.path)))

class TaggedLogicalModel(models.Model):

	model = models.ForeignKey(LogicalModel, on_delete=models.CASCADE)
	tag = models.CharField(max_length=256)

	file = models.FileField(upload_to=path_tagged_logical_model, blank=True)
	bnd_file = models.FileField(upload_to=path_tagged_logical_model, blank=True)
	cfg_file = models.FileField(upload_to=path_tagged_logical_model, blank=True)

pre_delete.connect(remove_tagged_logical_model, sender=TaggedLogicalModel)
	
# Demo models, from api/defaults/models : copied in the first project of every user, and in the
# demo project shown to anonymous users (the project of the guest account)
DEMO_MODELS = [
	("Cohen2015 - Tumour Cell Invasion and Migration", "metastasis"),
	("Corral2021 - Interplay between SMAD2 and STAT5A regulating IL-17A/F expression in Th cells", "corral"),
	("Sizek2019 - Growth signaling, cell cycle and apoptosis", "sizek"),
]

def add_demo_models(project):
	for name, directory in DEMO_MODELS:
		path = join(settings.BASE_DIR, "api", "defaults", "models", directory)
		with open(join(path, directory + ".bnd"), 'rb') as bnd_file, open(join(path, directory + ".cfg"), 'rb') as cfg_file:
			LogicalModel(
				project=project,
				name=name,
				bnd_file=File(bnd_file, name=directory + ".bnd"),
				cfg_file=File(cfg_file, name=directory + ".cfg"),
				format=LogicalModel.MABOSS
			).save()

def add_default_models(sender, instance, **kwargs):

	default_project = add_default_project(sender, instance, **kwargs)
	if default_project is not None:
		add_demo_models(default_project)



post_save.connect(add_default_models, sender=User)