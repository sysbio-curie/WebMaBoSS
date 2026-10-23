from django.core.files import File
from rest_framework import status

from api.tests import test_simulate
from api.tests.APITestCase import APITestCase
from api.models import LogicalModel, MaBoSSSensitivityAnalysis

from json import dumps, loads
from os.path import join, dirname
from unittest.mock import patch

FILES = join(dirname(__file__), 'files')


class NoThread:
	""" The analyses are only created : not run """
	def __init__(self, target, args):
		pass

	def start(self):
		pass


class TestLegacyFormats(APITestCase):
	"""
	Models uploaded before every upload was converted to MaBoSS are stored as they were : GINsim (zginml) or SBML
	files. They can still be exported in every format, and analysed.
	"""
	fixtures = test_simulate.TestSimulate.fixtures
	setUp = test_simulate.TestSimulate.setUp

	def legacy_models(self):
		project = self.projects[0]
		zginml = LogicalModel.objects.get(project=project, format=LogicalModel.ZGINML)
		with open(join(FILES, "Metastasis_Master_Model.sbml"), "rb") as sbml:
			sbml_model = LogicalModel(
				project=project, name="Metastasis SBML", format=LogicalModel.SBML,
				file=File(sbml, name="Metastasis_Master_Model.sbml")
			)
			sbml_model.save()
		return project, {"zginml": zginml, "sbml": sbml_model}

	def content(self, response):
		return b"".join(response.streaming_content) if response.streaming else response.content

	def testExports(self):
		self.login()
		project, models = self.legacy_models()

		# What each export starts with, or contains
		expected = {
			"file": b"PK", "sbmlfile": b"<sbml", "bndfile": b"Metastasis", "cfgfile": b"istate", "bnetfile": b"Metastasis",
		}
		for stored, model in models.items():
			for export, content in expected.items():
				request = self.client.get("/api/logical_models/%d/%d/%s" % (project.id, model.id, export))
				self.assertEqual(request.status_code, status.HTTP_200_OK, "%s model, %s export" % (stored, export))
				data = self.content(request)
				# The GINsim file of a converted model is GINML, which GINsim also opens, rather than zipped
				self.assertTrue(
					(data.startswith(content) or b"<gxl" in data[:1000]) if export == "file" else content in data,
					"%s model, %s export : %s" % (stored, export, data[:100])
				)

	def testSensitivityAnalysis(self):
		self.login()
		project, models = self.legacy_models()

		for stored, model in models.items():
			nodes = loads(self.client.get("/api/logical_model/%d/%d/maboss/settings/" % (project.id, model.id)).content)
			outputs = nodes["output_variables"]
			with patch("api.views.maboss.MaBoSSSensitivityAnalysisView.Thread", NoThread):
				request = self.client.post("/api/logical_model/%d/%d/maboss_sensitivity" % (project.id, model.id), {
					"settings": dumps({
						"name": stored + " analysis",
						"candidateVariables": {node: node in ("DNAdamage", "ECMicroenv") for node in outputs},
						"outputVariables": outputs,
						"singleMutations": {"on": True, "off": False},
						"doubleMutations": {"on": False, "off": False},
					})
				})
			self.assertEqual(request.status_code, status.HTTP_200_OK, stored + " model")
			self.assertTrue(MaBoSSSensitivityAnalysis.objects.filter(model=model).exists(), stored + " model")
