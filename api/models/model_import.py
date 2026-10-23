from django.db import models

from api.models.project import Project
from api.models.logical_model import LogicalModel
from api.models.TimeStampMixin import TimeStampMixin


class ModelImport(TimeStampMixin):
	""" A model imported from a public repository, in the background : some downloads take more than a minute """

	project = models.ForeignKey(Project, on_delete=models.CASCADE)

	repository = models.CharField(max_length=32)
	# Id of the model in the repository
	remote_id = models.CharField(max_length=256)
	name = models.CharField(max_length=256)
	use_sbml_names = models.BooleanField(default=True)

	BUSY = 'Running'
	ENDED = 'Finished'
	ERROR = 'Failed'

	STATUSES = (
		(BUSY, 'Busy'),
		(ENDED, 'Ended'),
		(ERROR, 'Error')
	)

	status = models.CharField(max_length=15, choices=STATUSES, default=BUSY)
	error = models.TextField(default="")

	# The model created, once imported
	model = models.ForeignKey(LogicalModel, null=True, on_delete=models.SET_NULL)
