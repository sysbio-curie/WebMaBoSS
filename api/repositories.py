"""
Public repositories of logical models, from which models can be imported in a project : BioModels, Cell Collective
and the model repository of GINsim. Their lists are kept for a while in the shared cache, as they rarely change and
are long to get, and the maintenance job (manage.py maintenance) gets them again regularly.
Only the models of these lists can be downloaded : the server never fetches an address given by a user.
"""

import io, re, zipfile
from html import unescape
from os.path import join
from urllib.parse import quote

import requests
from django.core.cache import caches

# Cell Collective takes up to a minute and a half to export a large model
DOWNLOAD_TIMEOUT = 180
LIST_TIMEOUT = 30
LIST_CACHED_FOR = 6 * 3600
# Got again by the maintenance job every hour, and kept longer : a repository unreachable for a while is still listed
LIST_KEPT_BY_MAINTENANCE = 2 * 24 * 3600
MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024


class RepositoryError(Exception):
	""" The repository couldn't be reached, or answered something unexpected """


def get(url, timeout, **kwargs):
	""" Downloads url, at most MAX_DOWNLOAD_SIZE of it """
	try:
		response = requests.get(url, timeout=timeout, stream=True, **kwargs)
		response.raise_for_status()
		content = b""
		for chunk in response.iter_content(chunk_size=1024 * 1024):
			content += chunk
			if len(content) > MAX_DOWNLOAD_SIZE:
				raise RepositoryError("the file is larger than %d MB" % (MAX_DOWNLOAD_SIZE // (1024 * 1024)))
		return content
	except requests.RequestException as e:
		raise RepositoryError(str(e))


def get_json(url, **kwargs):
	try:
		return requests.get(url, timeout=LIST_TIMEOUT, **kwargs).json()
	except (requests.RequestException, ValueError) as e:
		raise RepositoryError(str(e))


class Repository:
	key = None
	title = None
	# Format of the files : "sbml" or "zginml"
	format = None

	def models(self):
		""" The models of the repository : dicts with at least id, name and author """
		models = caches["shared"].get("repository-" + self.key)
		if models is None:
			models = self.refresh()
		return models

	def refresh(self, kept=LIST_CACHED_FOR):
		""" Gets the list of the models again, and keeps it in the shared cache """
		try:
			models = self.list_models()
		except (KeyError, TypeError, AttributeError, IndexError) as e:
			raise RepositoryError("unexpected answer (%s)" % e)
		caches["shared"].set("repository-" + self.key, models, kept)
		return models

	def find(self, model_id):
		return next((model for model in self.models() if model["id"] == model_id), None)

	def list_models(self):
		raise NotImplementedError

	def download(self, model, folder):
		""" Downloads a model of the list in folder, and returns the path of its file """
		raise NotImplementedError


class BioModels(Repository):
	key = "biomodels"
	title = "BioModels"
	format = "sbml"

	URL = "https://www.biomodels.org"
	QUERY = 'modellingapproach:"logical model" OR modellingapproach:"boolean model"'
	PAGE = 100

	def list_models(self):
		models = []
		while True:
			data = get_json(self.URL + "/search", params={
				"query": self.QUERY, "numResults": self.PAGE, "offset": len(models), "format": "json"
			}, headers={"accept": "application/json"})
			page = data["models"]
			models += page
			if len(page) < self.PAGE or len(models) >= data["matches"]:
				break

		return [
			{"id": model["id"], "name": model["name"], "author": model.get("submitter") or "",
			 "url": self.URL + "/" + model["id"]}
			for model in models if model.get("format") == "SBML"
		]

	def download(self, model, folder):
		content = get(self.URL + "/search/download", DOWNLOAD_TIMEOUT, params={"models": model["id"]})
		try:
			archive = zipfile.ZipFile(io.BytesIO(content))
		except zipfile.BadZipFile:
			raise RepositoryError("BioModels didn't send an archive")

		# The model, and sometimes other files (figures, simulations...)
		names = [name for name in archive.namelist() if name.lower().endswith((".xml", ".sbml"))]
		names.sort(key=lambda name: name.split("/")[-1] != model["id"] + ".xml")
		if len(names) == 0:
			raise RepositoryError("no SBML file in the archive of %s" % model["id"])

		path = join(folder, "model.sbml")
		with open(path, "wb") as sbml_file:
			sbml_file.write(archive.read(names[0]))
		return path


class CellCollective(Repository):
	key = "cellcollective"
	title = "Cell Collective"
	format = "sbml"

	URL = "https://research.cellcollective.org/web"

	def list_models(self):
		count = get_json(self.URL + "/_api/model/cards/count/research", params={"modelTypes": "boolean"})
		cards = get_json(self.URL + "/api/model/cards/research", params={
			"category": "published", "orderBy": "recent", "modelTypes": "boolean", "cards": count["published"]
		})
		return [
			{"id": str(card["model"]["id"]), "name": re.sub(r"\.sbml$", "", card["model"]["name"].strip()),
			 "author": card["model"].get("author") or "", "version": str(card["model"].get("selectedVersion") or 1)}
			for card in cards
		]

	def download(self, model, folder):
		content = get(self.URL + "/_api/model/export/" + model["id"], DOWNLOAD_TIMEOUT,
			params={"version": model["version"], "type": "SBML"})
		path = join(folder, "model.sbml")
		with open(path, "wb") as sbml_file:
			sbml_file.write(content)
		return path


class GINsim(Repository):
	key = "ginsim"
	title = "GINsim"
	format = "zginml"

	SITE = "https://ginsim.github.io/models/"
	# The sources of the site, where the files of each model are
	TREE = "https://api.github.com/repos/GINsim/GINsim.github.io/git/trees/HEAD?recursive=1"

	def list_models(self):
		try:
			html = requests.get(self.SITE, timeout=LIST_TIMEOUT).text
		except requests.RequestException as e:
			raise RepositoryError(str(e))

		# The table of the models : name (with the link to its page), taxon, process, year, authors
		pages = {}
		for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
			cells = re.findall(r"<td>(.*?)</td>", row, re.S)
			link = re.match(r'\s*<a href="([^"/]+)/">(.*?)</a>', cells[0]) if len(cells) == 5 else None
			if link:
				pages[link.group(1)] = {
					"title": unescape(re.sub(r"<[^>]+>", "", link.group(2))).strip(),
					"year": unescape(cells[3]).strip(), "author": unescape(cells[4]).strip()
				}

		# Without a token, GitHub answers 60 requests per hour : the list is kept for a while
		tree = get_json(self.TREE, headers={"accept": "application/vnd.github+json"})
		if "tree" not in tree:
			raise RepositoryError(tree.get("message", "no list of files"))

		files = {}
		for entry in tree["tree"]:
			match = re.fullmatch(r"docs/models/([^/]+)/([^/]+\.zginml)", entry["path"])
			if entry["type"] == "blob" and match:
				files.setdefault(match.group(1), []).append(match.group(2))

		models = []
		for page, names in sorted(files.items()):
			info = pages.get(page, {"title": page, "year": "", "author": ""})
			for name in sorted(names):
				models.append({
					"id": page + "/" + name,
					"name": info["title"] + (" (%s)" % name if len(names) > 1 else ""),
					"author": info["author"], "year": info["year"], "url": self.SITE + page + "/"
				})
		return models

	def download(self, model, folder):
		content = get(self.SITE + quote(model["id"]), DOWNLOAD_TIMEOUT)
		path = join(folder, "model.zginml")
		with open(path, "wb") as ginsim_file:
			ginsim_file.write(content)
		return path


REPOSITORIES = {repository.key: repository for repository in (BioModels(), CellCollective(), GINsim())}
