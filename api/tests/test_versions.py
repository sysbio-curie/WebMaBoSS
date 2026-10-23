from django.conf import settings
from rest_framework import status

from api.tests.APITestCase import APITestCase

from json import load, loads
from os.path import join


class TestVersions(APITestCase):

	def testVersions(self):
		# For everyone, on the About page
		request = self.client.get("/api/versions")
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		versions = loads(request.content)

		with open(join(settings.BASE_DIR, "package.json")) as package:
			self.assertEqual(versions["WebMaBoSS"], load(package)["version"])
		self.assertEqual(sorted(versions), ["GINsim", "MaBoSS", "WebMaBoSS", "pyMaBoSS"])
		# In the image, the tools come from conda (MaBoSS, GINsim) and pip (pyMaBoSS, from a commit of GitHub)
		self.assertTrue(all(versions.values()), versions)
