from django.conf import settings
from django.core.cache import cache
from rest_framework import status

from api.tests.APITestCase import APITestCase
from api.models import LogicalModel, ModelImport
from api.models.common import create_guest_account

from io import BytesIO
from json import loads
from os.path import join, dirname
from os import makedirs
from unittest.mock import patch
import zipfile
import requests

FILES = join(dirname(__file__), 'files')


class FakeResponse:
	def __init__(self, content=b"", data=None, status_code=200):
		self.content, self.data, self.status_code = content, data, status_code
		self.text = content.decode(errors="replace")

	def json(self):
		return self.data

	def raise_for_status(self):
		if self.status_code >= 400:
			raise requests.HTTPError("%d error" % self.status_code)

	def iter_content(self, chunk_size):
		yield self.content


def sbml_archive(name):
	content = BytesIO()
	with zipfile.ZipFile(content, "w") as archive:
		archive.writestr("figure.png", b"not a model")
		with open(join(FILES, "Metastasis_Master_Model.sbml"), "rb") as sbml:
			archive.writestr(name + ".xml", sbml.read())
	return content.getvalue()


GINSIM_SITE = """<table><thead><tr><th>Model name</th><th>Taxon</th><th>Process</th><th>Year</th><th>Author(s)</th></tr></thead>
<tbody>
<tr>
<td><a href="2017-metastasis/">Metastasis &amp; invasion</a></td>
<td>Mammal</td>
<td>Cancer</td>
<td>2017</td>
<td>Cohen, David</td>
</tr>
</tbody></table>"""

GINSIM_TREE = {"tree": [
	{"type": "blob", "path": "docs/models/2017-metastasis/index.md"},
	{"type": "blob", "path": "docs/models/2017-metastasis/Metastasis.zginml"},
	{"type": "blob", "path": "docs/models/2017-metastasis/Metastasis_reduced.zginml"},
	{"type": "blob", "path": "docs/models/2020-new/model.zginml"},
	{"type": "blob", "path": "docs/index.md"},
]}


class FakeRepositories:
	""" Answers the requests to the repositories, and records them """

	def __init__(self):
		self.urls = []
		self.fail_downloads = False

	def get(self, url, params=None, **kwargs):
		self.urls.append(url)
		params = params or {}

		if url == "https://www.biomodels.org/search":
			return FakeResponse(data={"matches": 2, "models": [
				{"id": "MODEL0000000001", "name": "Metastasis model", "submitter": "Someone", "format": "SBML"},
				{"id": "MODEL0000000002", "name": "A python model", "submitter": "Someone", "format": "Python"},
			]})
		if url == "https://www.biomodels.org/search/download":
			if self.fail_downloads:
				return FakeResponse(status_code=503)
			return FakeResponse(content=sbml_archive(params["models"]))

		if url.endswith("/_api/model/cards/count/research"):
			return FakeResponse(data={"published": 1})
		if url.endswith("/api/model/cards/research"):
			return FakeResponse(data=[{"model": {"id": 2176, "name": "T-LGL.sbml", "author": None, "selectedVersion": "3"}}])
		if "/_api/model/export/" in url:
			with open(join(FILES, "Metastasis_Master_Model.sbml"), "rb") as sbml:
				return FakeResponse(content=sbml.read())

		if url == "https://ginsim.github.io/models/":
			return FakeResponse(content=GINSIM_SITE.encode())
		if url.startswith("https://api.github.com/"):
			return FakeResponse(data=GINSIM_TREE)
		if url.startswith("https://ginsim.github.io/models/"):
			with open(join(FILES, "Metastasis_Master_Model.zginml"), "rb") as model:
				return FakeResponse(content=model.read())

		raise AssertionError("Unexpected request to " + url)


class SynchronousThread:
	""" Runs the import in the test, instead of in a thread which wouldn't see the test's database """
	def __init__(self, target, args):
		self.target, self.args = target, args

	def start(self):
		self.target(*self.args)


class TestRepositories(APITestCase):
	fixtures = ['project.json']

	def setUp(self):
		APITestCase.setUp(self)
		makedirs(join(settings.MEDIA_ROOT, "zS2NSxM9A4I0"), exist_ok=True)
		create_guest_account()
		cache.clear()

		self.fake = FakeRepositories()
		for target, replacement in [
			("api.repositories.requests.get", self.fake.get),
			("api.views.Repositories.Thread", SynchronousThread),
		]:
			patcher = patch(target, replacement)
			patcher.start()
			self.addCleanup(patcher.stop)

	def models(self, repository):
		request = self.client.get("/api/repositories/%s/" % repository)
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		return loads(request.content)

	def importModel(self, repository, model_id, name="Imported"):
		request = self.client.post("/api/repositories/%s/1/import" % repository, {
			"model_id": model_id, "name": name, "use_sbml_names": "true"
		})
		if request.status_code != status.HTTP_200_OK:
			return request.status_code, None
		import_id = loads(request.content)["import_id"]
		request = self.client.get("/api/repositories/imports/1/%d" % import_id)
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		return request.status_code, loads(request.content)

	def testLists(self):
		# Only the SBML models of BioModels
		self.assertEqual(self.models("biomodels"), [{
			"id": "MODEL0000000001", "name": "Metastasis model", "author": "Someone",
			"url": "https://www.biomodels.org/MODEL0000000001"
		}])
		# Kept for a while
		requests_made = len(self.fake.urls)
		self.models("biomodels")
		self.assertEqual(len(self.fake.urls), requests_made)

		self.assertEqual(self.models("cellcollective"), [
			{"id": "2176", "name": "T-LGL", "author": "", "version": "3"}
		])

		# A model per file, named after the table of the site
		self.assertEqual([(model["id"], model["name"], model["author"]) for model in self.models("ginsim")], [
			("2017-metastasis/Metastasis.zginml", "Metastasis & invasion (Metastasis.zginml)", "Cohen, David"),
			("2017-metastasis/Metastasis_reduced.zginml", "Metastasis & invasion (Metastasis_reduced.zginml)", "Cohen, David"),
			("2020-new/model.zginml", "2020-new", ""),
		])

		request = self.client.get("/api/repositories/unknown/")
		self.assertEqual(request.status_code, status.HTTP_404_NOT_FOUND)

	def testImport(self):
		self.login()

		for repository, model_id in [
			("biomodels", "MODEL0000000001"), ("cellcollective", "2176"), ("ginsim", "2017-metastasis/Metastasis.zginml")
		]:
			code, result = self.importModel(repository, model_id, name=repository + " model")
			self.assertEqual(code, status.HTTP_200_OK)
			self.assertEqual(result["error"], "")
			self.assertTrue(result["done"])
			model = LogicalModel.objects.get(id=result["model"])
			self.assertEqual((model.name, model.project.id, model.format), (repository + " model", 1, LogicalModel.MABOSS))

			# A model which can be simulated
			request = self.client.get("/api/logical_model/1/%d/maboss/settings/" % model.id)
			self.assertEqual(request.status_code, status.HTTP_200_OK)
			self.assertIn("Metastasis", loads(request.content)["output_variables"])

		self.assertIn("https://research.cellcollective.org/web/_api/model/export/2176", self.fake.urls)

	def testImportErrors(self):
		self.login()

		# Only the models of the lists : the server never downloads an address given by a user
		code, _ = self.importModel("biomodels", "https://example.org/model.sbml")
		self.assertEqual(code, status.HTTP_400_BAD_REQUEST)
		self.assertNotIn("https://example.org/model.sbml", self.fake.urls)

		self.fake.fail_downloads = True
		code, result = self.importModel("biomodels", "MODEL0000000001")
		self.assertEqual(code, status.HTTP_200_OK)
		self.assertTrue(result["failed"])
		self.assertIn("Could not download the model from BioModels", result["error"])
		self.assertEqual(LogicalModel.objects.filter(project__id=1).count(), 0)

	def testAnonymousCannotImport(self):
		code, _ = self.importModel("biomodels", "MODEL0000000001")
		self.assertEqual(code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(ModelImport.objects.count(), 0)
