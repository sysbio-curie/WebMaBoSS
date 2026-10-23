"""
Versions of WebMaBoSS and of the tools it uses, shown on the About page
"""

import json
import re
import sys
from functools import lru_cache
from glob import glob
from importlib import metadata
from os.path import join

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def conda_version(package):
	""" Version of a conda package of the environment, if it was installed with conda """
	for path in glob(join(sys.prefix, "conda-meta", package + "-*.json")):
		with open(path) as meta:
			data = json.load(meta)
		if data.get("name") == package:
			return data.get("version")
	return None


def python_version(distribution):
	""" Version of a python package, with the commit it was installed from when it comes from GitHub """
	try:
		dist = metadata.distribution(distribution)
	except metadata.PackageNotFoundError:
		return None

	version = dist.version
	origin = json.loads(dist.read_text("direct_url.json") or "{}").get("url", "")
	match = re.search(r"github\.com/([^/]+/[^/]+)/archive/([0-9a-f]{40})", origin)
	if match:
		version += " (%s@%s)" % (match.group(1), match.group(2)[:8])
	return version


@lru_cache(maxsize=None)
def versions():
	with open(join(settings.BASE_DIR, "package.json")) as package:
		webmaboss = json.load(package)["version"]

	return {
		"WebMaBoSS": webmaboss,
		"MaBoSS": conda_version("maboss"),
		"pyMaBoSS": python_version("maboss"),
		"GINsim": conda_version("ginsim"),
	}


class Versions(APIView):
	permission_classes = (AllowAny,)

	def get(self, request):
		return Response(versions())
