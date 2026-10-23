#!/usr/bin/env python3
"""
End-to-end smoke test of a running WebMaBoSS instance, through its HTTP API.

It goes through what a user does from the web interface: register, login,
create a project, import models in every supported format, browse and edit
them, run a MaBoSS simulation and a sensitivity analysis, read all results,
export files, and clean everything up.

Every response is recorded (status code and normalized body) into a snapshot.
Snapshots taken on a reference version are then compared with snapshots taken
on an upgraded version:

    # Two runs on the reference version, to find out what is non-deterministic
    api_smoke.py --url http://reference:8000 --out ref1.json
    api_smoke.py --url http://reference:8000 --out ref2.json
    # One run on the new version, compared to the reference
    api_smoke.py --url http://new:8000 --out new.json --compare ref1.json ref2.json

Values which are identical in both reference runs must be identical in the new
run (floats with a tolerance). Values which differ between reference runs
(ids, dates, random file names...) are only compared by structure. Simulation
results are stochastic : probabilities are compared with a tolerance, and the
other results (fixed points, PCA, sensitivity analysis) only by structure.

Only depends on `requests`.
"""

import argparse
import json
import os
import re
import sys
import time
import uuid

import requests

FILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api", "tests", "files")


class Smoke:

	def __init__(self, url, timeout):
		self.url = url.rstrip("/")
		self.timeout = timeout
		self.session = requests.Session()
		self.records = {}
		self.failures = []
		self.replacements = {}

	# --------------------------------------------------------------------------------------------
	# Helpers

	def placeholder(self, value, name):
		""" Registers a run-specific value (id, token, username...) to be hidden in the snapshot """
		if value is not None and str(value) != "":
			# Ids of different tables can be equal : they all get the same placeholder
			self.replacements[str(value)] = "<id>" if str(value).isdigit() else "<%s>" % name

	def request(self, step, method, path, expect=(200,), record=True, **kwargs):
		try:
			response = self.session.request(method, self.url + path, timeout=300, **kwargs)
		except requests.RequestException as e:
			self.failures.append("%s: %s %s raised %s" % (step, method, path, e))
			self.records[step] = {"status": None, "body": str(e)}
			return None

		if expect is not None and response.status_code not in expect:
			self.failures.append("%s: %s %s returned %d (expected %s): %s" % (
				step, method, path, response.status_code, expect, response.text[:300]
			))

		if record:
			self.records[step] = {"status": response.status_code, "body": self.body(response)}
		return response

	@staticmethod
	def body(response):
		content_type = response.headers.get("Content-Type", "")
		if "json" in content_type:
			try:
				return response.json()
			except ValueError:
				pass
		if "html" in content_type:
			# Django debug/error pages are huge and full of run-specific data
			title = re.search(r"<title>(.*?)</title>", response.text, re.S)
			return {"html_title": title.group(1).strip() if title else None}
		try:
			return {"text": response.content.decode()}
		except UnicodeDecodeError:
			return {"binary_size": len(response.content)}

	def wait(self, step, path, is_done):
		start = time.time()
		while time.time() - start < self.timeout:
			response = self.request(step, "get", path, record=False)
			if response is None or response.status_code != 200:
				break
			status = response.json()
			if status.get("failed"):
				self.failures.append("%s: failed (%s)" % (step, status))
				break
			if is_done(status):
				self.records[step] = {"status": response.status_code, "body": status}
				return True
			time.sleep(1)
		else:
			self.failures.append("%s: not finished after %ds" % (step, self.timeout))
		return False

	# --------------------------------------------------------------------------------------------
	# Scenario

	def run(self):

		self.request("index", "get", "/")
		self.request("static_js", "get", "/static/js/index.js", record=False)
		self.request("anonymous_is_logged_in", "get", "/api/auth/is_logged_in", expect=None)
		self.request("anonymous_projects", "get", "/api/projects/", expect=None)
		self.demo()

		# Authentication
		username = "smoke_" + uuid.uuid4().hex[:10]
		password, new_password = "Smoke-" + uuid.uuid4().hex, "Smoke-" + uuid.uuid4().hex
		self.placeholder(username, "username")

		response = self.request("register", "post", "/api/auth/register", data={
			"username": username, "email": username + "@example.org",
			"password1": password, "password2": password,
		}, expect=(200, 201))
		if response is None or "key" not in response.json():
			self.failures.append("register: no token, stopping")
			return
		self.placeholder(response.json()["key"], "register_token")

		self.request("logout_after_register", "post", "/api/auth/logout",
			headers={"Authorization": "Token " + response.json()["key"]})

		response = self.request("login", "post", "/api/auth/login", data={"username": username, "password": password})
		self.login(response)
		self.request("login_wrong_password", "post", "/api/auth/login",
			data={"username": username, "password": "wrong"}, expect=(400,), headers={"Authorization": ""})

		self.request("is_logged_in", "get", "/api/auth/is_logged_in")
		self.request("email", "get", "/api/auth/email")
		self.request("password_change", "post", "/api/auth/password/change", data={
			"old_password": password, "new_password1": new_password, "new_password2": new_password,
		})
		self.request("logout", "post", "/api/auth/logout")
		self.session.headers.pop("Authorization", None)
		response = self.request("login_new_password", "post", "/api/auth/login",
			data={"username": username, "password": new_password})
		self.login(response)

		# Projects
		response = self.request("projects", "get", "/api/projects/")
		for i, project in enumerate(response.json() if response is not None else []):
			self.placeholder(project.get("id"), "project_id_%d" % i)
			self.placeholder(project.get("path"), "project_path_%d" % i)

		self.request("project_create", "post", "/api/projects/",
			data={"name": "smoke project", "description": "created by api_smoke.py"})
		response = self.request("projects_after_create", "get", "/api/projects/")
		projects = response.json() if response is not None else []
		project = [p for p in projects if p["name"] == "smoke project"]
		if len(project) != 1:
			self.failures.append("project_create: project not found, stopping")
			return
		project_id = project[0]["id"]
		self.placeholder(project_id, "project_id")
		self.placeholder(project[0].get("path"), "project_path")
		self.request("project", "get", "/api/projects/%d" % project_id)

		# Model imports
		models = "/api/logical_models/%d/" % project_id
		imports = [
			("zginml", "Metastasis_Master_Model.zginml", "Metastasis_Master_Model.zginml", {}),
			("zginml_flobak", "Flobak2015_full_journal.pcbi.1004426.s003.ZGINML", "flobak.zginml", {}),
			("sbml", "Metastasis_Master_Model.sbml", "Metastasis_Master_Model.sbml", {"use_sbml_names": "false"}),
			("sbml_names", "Metastasis_Master_Model.sbml", "Metastasis_Master_Model.sbml", {"use_sbml_names": "true"}),
		]
		for name, filename, upload_name, data in imports:
			with open(os.path.join(FILES, filename), "rb") as f:
				self.request("import_" + name, "post", models,
					data=dict(data, name="smoke " + name), files={"file": (upload_name, f)})

		model_ids = self.list_models(project_id, "models_after_imports")

		# Browsing every imported model
		for name, model_id in sorted(model_ids.items()):
			self.browse_model(project_id, model_id, name)

		# Round trips : re-importing exported files
		metastasis = model_ids["smoke zginml"]
		base = "/api/logical_models/%d/%d" % (project_id, metastasis)
		bnet = self.request("export_bnet", "get", base + "/bnetfile", record=False)
		bnd = self.request("export_bnd", "get", base + "/bndfile", record=False)
		cfg = self.request("export_cfg", "get", base + "/cfgfile", record=False)
		sbml = self.request("export_sbml", "get", base + "/sbmlfile", record=False)

		if bnet is not None and bnet.status_code == 200:
			self.request("import_bnet", "post", models, data={"name": "smoke bnet"},
				files={"file": ("model.bnet", bnet.content)})
		if bnd is not None and cfg is not None and bnd.status_code == 200 and cfg.status_code == 200:
			self.request("import_maboss", "post", models, data={"name": "smoke maboss"},
				files={"file": ("model.bnd", bnd.content), "file2": ("model.cfg", cfg.content)})
		if sbml is not None and sbml.status_code == 200:
			self.request("import_exported_sbml", "post", models, data={"name": "smoke exported sbml", "use_sbml_names": "false"},
				files={"file": ("model.sbml", sbml.content)})

		model_ids = self.list_models(project_id, "models_after_round_trips")
		for name in ["smoke bnet", "smoke maboss", "smoke exported sbml"]:
			if name in model_ids:
				self.browse_model(project_id, model_ids[name], name)
			else:
				self.failures.append("round trip: model '%s' missing" % name)

		# Edition, tags, simulations, sensitivity analysis : one model per stored format
		for name in ["smoke zginml", "smoke sbml", "smoke maboss"]:
			if name in model_ids:
				self.edit_model(project_id, model_ids[name], name)
				self.simulate(project_id, model_ids[name], name)
				self.sensitivity(project_id, model_ids[name], name)

		# Restoring the demo models in the project
		self.request("restore_demo_models", "post", "/api/projects/%d/demo_models" % project_id)
		model_ids = self.list_models(project_id, "models_after_restore")

		# Cleanup
		for name, model_id in sorted(model_ids.items()):
			self.request("delete_model %s" % name, "delete", "/api/logical_models/%d/%d" % (project_id, model_id))
		self.request("models_after_delete", "get", models)
		self.request("project_delete", "delete", "/api/projects/%d" % project_id)
		self.request("logout_end", "post", "/api/auth/logout")

	def demo(self):
		""" Anonymous users can look at the demo project and run simulations, but can't modify it """

		# The project id doesn't matter, anonymous users always get the demo project
		response = self.request("anonymous demo models", "get", "/api/logical_models/0/")
		demo = response.json() if response is not None else []
		if len(demo) == 0:
			self.failures.append("anonymous demo models: no model, stopping the demo checks")
			return
		for i, model in enumerate(demo):
			self.placeholder(model["id"], "demo_model_%d" % i)
		model = "/api/logical_model/0/%d" % demo[0]["id"]
		files = "/api/logical_models/0/%d" % demo[0]["id"]

		forbidden = (403,)
		self.request("anonymous delete demo model", "delete", files, expect=forbidden)
		with open(os.path.join(FILES, "Metastasis_Master_Model.zginml"), "rb") as f:
			self.request("anonymous add demo model", "post", "/api/logical_models/0/", expect=forbidden,
				data={"name": "anonymous model", "use_sbml_names": "false"}, files={"file": ("model.zginml", f)})
		self.request("anonymous rename demo model", "post", model + "/name", data={"name": "renamed"}, expect=forbidden)
		self.request("anonymous edit demo formula", "post", model + "/formula/CDH1/logic", data={"formula": "1"}, expect=forbidden)
		self.request("anonymous edit demo settings", "put", model + "/settings", data={"settings": "{}"}, expect=forbidden)
		self.request("anonymous restore demo models", "post", "/api/projects/0/demo_models", expect=forbidden)
		self.request("anonymous demo models after", "get", "/api/logical_models/0/")

		# Simulations are allowed, and cleaned after a day
		response = self.request("anonymous simulation settings", "get", model + "/maboss/settings/")
		if response is None or response.status_code != 200:
			return
		defaults = response.json()
		name = "anonymous smoke " + uuid.uuid4().hex
		self.request("anonymous simulation create", "post", model + "/maboss", data={
			"name": name,
			"settings": json.dumps(dict(defaults["settings"], sample_count=1000, max_time=10)),
			"initialStates": json.dumps(defaults["initial_states"]),
			"outputVariables": json.dumps(defaults["output_variables"]),
			"mutations": json.dumps({}),
		})
		# Simulations of all anonymous users are listed : not recorded
		response = self.request("anonymous simulations", "get", model + "/maboss", record=False)
		simulations = [s for s in (response.json() if response is not None else []) if s["name"] == name]
		if len(simulations) != 1:
			self.failures.append("anonymous simulation: not found")
			return
		self.placeholder(simulations[0]["id"], "anonymous_simulation_id")
		simulation = "/api/maboss/0/%d" % simulations[0]["id"]
		self.wait("anonymous simulation status", simulation + "/status", lambda s: s.get("done"))
		self.request("anonymous simulation nodes_trajs/", "get", simulation + "/nodes_trajs/")
		self.request("anonymous simulation new model", "get", simulation + "/new_model", expect=forbidden)

	def login(self, response):
		if response is None or response.status_code != 200:
			raise SystemExit("Login failed: " + (response.text if response is not None else "no response"))
		token = response.json()["key"]
		self.placeholder(token, "token")
		self.session.headers["Authorization"] = "Token " + token

	def list_models(self, project_id, step):
		response = self.request(step, "get", "/api/logical_models/%d/" % project_id)
		model_ids = {}
		for model in (response.json() if response is not None else []):
			model_ids[model["name"]] = model["id"]
			self.placeholder(model["id"], "model_id[%s]" % model["name"])
		return model_ids

	def browse_model(self, project_id, model_id, name):
		files = "/api/logical_models/%d/%d" % (project_id, model_id)
		model = "/api/logical_model/%d/%d" % (project_id, model_id)

		self.request("%s model" % name, "get", files)
		for endpoint in ["file", "sbmlfile", "bndfile", "cfgfile", "bnetfile"]:
			self.request("%s %s" % (name, endpoint), "get", "%s/%s" % (files, endpoint), expect=None)
		for endpoint in ["name", "nodes", "graph", "graph_raw", "formulas", "parameters",
						 "initial_states", "outputs", "settings", "maboss/settings/", "steady_states"]:
			self.request("%s %s" % (name, endpoint), "get", "%s/%s" % (model, endpoint), expect=None)

	def edit_model(self, project_id, model_id, name):
		files = "/api/logical_models/%d/%d" % (project_id, model_id)
		model = "/api/logical_model/%d/%d" % (project_id, model_id)

		self.request("%s rename" % name, "post", model + "/name", data={"name": name + " renamed"}, expect=None)
		self.request("%s rename back" % name, "post", model + "/name", data={"name": name}, expect=None)

		self.request("%s tag" % name, "post", files + "/tags/", data={"tag": "v1"}, expect=None)
		self.request("%s tags" % name, "get", files + "/tags/", expect=None)
		self.request("%s tag get" % name, "get", files + "/tags/v1", expect=None)
		self.request("%s tag delete" % name, "delete", files + "/tags/v1", expect=None)
		self.request("%s tags after delete" % name, "get", files + "/tags/", expect=None)

		self.request("%s check formula ok" % name, "post", model + "/check_formula/Metastasis/rate_up",
			data={"formula": "1.0"}, expect=None)
		self.request("%s check formula ko" % name, "post", model + "/check_formula/Metastasis/rate_up",
			data={"formula": "1.0 +* "}, expect=None)

		response = self.request("%s settings before" % name, "get", model + "/settings", expect=None)
		if response is not None and response.status_code == 200:
			settings = response.json()["settings"]
			self.request("%s settings update" % name, "put", model + "/settings",
				data={"settings": json.dumps(settings)}, expect=None)
		self.request("%s settings after" % name, "get", model + "/settings", expect=None)

	def simulate(self, project_id, model_id, name):
		model = "/api/logical_model/%d/%d" % (project_id, model_id)
		response = self.request("%s simulation settings" % name, "get", model + "/maboss/settings/")
		if response is None or response.status_code != 200:
			return
		defaults = response.json()

		settings = dict(defaults["settings"])
		settings.update({"sample_count": 1000, "max_time": 10, "seed_pseudorandom": 42})
		# The observed graph of the first three nodes
		observed = {node: i < 3 for i, node in enumerate(defaults.get("observed_graph_nodes", {}))}

		self.request("%s simulation create" % name, "post", model + "/maboss", data={
			"name": "smoke simulation",
			"settings": json.dumps(settings),
			"initialStates": json.dumps(defaults["initial_states"]),
			"outputVariables": json.dumps(defaults["output_variables"]),
			"observedGraphNodes": json.dumps(observed),
			"mutations": json.dumps({"Metastasis": "OFF"}),
		})

		response = self.request("%s simulations" % name, "get", model + "/maboss")
		simulations = response.json() if response is not None else []
		if len(simulations) != 1:
			self.failures.append("%s: expected one simulation, got %d" % (name, len(simulations)))
			return
		simulation_id = simulations[0]["id"]
		self.placeholder(simulation_id, "simulation_id")

		simulation = "/api/maboss/%d/%d" % (project_id, simulation_id)
		self.wait("%s simulation status" % name, simulation + "/status", lambda s: s.get("done"))

		for endpoint in ["fixed_points/", "last_states/", "states_trajs/", "nodes_trajs/", "observed_graph/", "pca", "sspca",
						 "bnd_file", "cfg_file"]:
			self.request("%s simulation %s" % (name, endpoint), "get", "%s/%s" % (simulation, endpoint), expect=None)

		self.request("%s simulation new model" % name, "get", simulation + "/new_model", expect=None)
		self.request("%s simulation delete" % name, "delete", simulation + "/")
		self.request("%s simulations after delete" % name, "get", model + "/maboss")

	def sensitivity(self, project_id, model_id, name):
		model = "/api/logical_model/%d/%d" % (project_id, model_id)
		response = self.request("%s sensitivity nodes" % name, "get", model + "/maboss/settings/")
		if response is None or response.status_code != 200:
			return
		outputs = response.json()["output_variables"]
		candidates = ["DNAdamage", "ECMicroenv", "TGFbeta"]

		self.request("%s sensitivity create" % name, "post", model + "/maboss_sensitivity", data={"settings": json.dumps({
			"name": "smoke sensitivity",
			"candidateVariables": {node: node in candidates for node in outputs},
			"outputVariables": outputs,
			"singleMutations": {"on": True, "off": True},
			"doubleMutations": {"on": False, "off": False},
		})})

		response = self.request("%s sensitivity list" % name, "get", model + "/maboss_sensitivity")
		analyses = response.json() if response is not None else []
		if len(analyses) != 1:
			self.failures.append("%s: expected one sensitivity analysis, got %d" % (name, len(analyses)))
			return
		analysis_id = analyses[0]["id"]
		self.placeholder(analysis_id, "analysis_id")

		analysis = "/api/maboss_sensitivity/%d/%d" % (project_id, analysis_id)
		self.wait("%s sensitivity status" % name, analysis + "/status", lambda s: s.get("done") == 1)
		self.request("%s sensitivity steady states" % name, "get", analysis + "/steady_states/", expect=None)
		self.request("%s sensitivity delete" % name, "delete", analysis + "/")

	# --------------------------------------------------------------------------------------------
	# Snapshot

	def snapshot(self):
		# Longest first, so that "12" doesn't replace part of "123"
		values = sorted(self.replacements, key=len, reverse=True)
		# Numeric ids are small on an empty database : they are only replaced in urls, like /api/maboss/3/12/
		patterns = [(
			re.compile(r'(?<=/)%s(?=/|$)' % v if v.isdigit() else r'(?<![\w.])%s(?![\w.])' % re.escape(v)),
			self.replacements[v]
		) for v in values]
		date = re.compile(r'\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)?')
		# Directories of projects and models, which are random, in urls of files
		media = re.compile(r'(?<=/media/)[A-Za-z0-9]{12}(?=/)|(?<=/logical_models/)[A-Za-z0-9]{12}(?=/)')

		def normalize(value, key=None):
			if isinstance(value, dict):
				# Keys are left untouched : they are node names, states, time points...
				return {k: normalize(v, k) for k, v in value.items()}
			if isinstance(value, list):
				return [normalize(v, key) for v in value]
			if isinstance(value, int) and not isinstance(value, bool):
				# Integers are only hidden when they are ids
				if key is not None and (key in ("id", "project", "model", "user") or key.endswith("_id")):
					return self.replacements.get(str(value), value)
				return value
			if isinstance(value, str):
				for pattern, replacement in patterns:
					value = pattern.sub(replacement, value)
				if key == "path" and re.fullmatch(r'[A-Za-z0-9]{12}', value):
					return "<path>"
				return media.sub("<path>", date.sub("<date>", value))
			return value

		return normalize(self.records)


# ------------------------------------------------------------------------------------------------
# Comparison

def shape(value):
	if isinstance(value, dict):
		return {k: shape(v) for k, v in value.items()}
	if isinstance(value, list):
		return ["list", len(value)] + ([shape(value[0])] if value else [])
	if isinstance(value, bool) or value is None:
		return value
	if isinstance(value, (int, float)):
		return "number"
	return type(value).__name__


def equal(a, b, tolerance=1e-6):
	# In python True == 1, but true and 1 are different for the javascript of the interface
	if isinstance(a, bool) != isinstance(b, bool):
		return False
	if isinstance(a, dict) and isinstance(b, dict):
		return a.keys() == b.keys() and all(equal(a[k], b[k], tolerance) for k in a)
	if isinstance(a, list) and isinstance(b, list):
		return len(a) == len(b) and all(equal(x, y, tolerance) for x, y in zip(a, b))
	if isinstance(a, float) or isinstance(b, float):
		try:
			return abs(float(a) - float(b)) <= tolerance * max(1.0, abs(float(a)))
		except (TypeError, ValueError):
			return False
	return a == b


def compare(new, ref1, ref2, path="", differences=None):
	""" Compares new with ref1, strictly where ref1 == ref2, by structure elsewhere """
	if differences is None:
		differences = []

	if equal(ref1, ref2):
		if not equal(new, ref1):
			differences.append((path, "value", ref1, new))
		return differences

	if isinstance(ref1, dict) and isinstance(ref2, dict) and isinstance(new, dict) and ref1.keys() == ref2.keys():
		if new.keys() != ref1.keys():
			differences.append((path, "keys", sorted(ref1.keys()), sorted(new.keys())))
		for key in ref1.keys() & new.keys():
			compare(new[key], ref1[key], ref2[key], "%s/%s" % (path, key), differences)
		return differences

	if isinstance(ref1, list) and isinstance(ref2, list) and isinstance(new, list) and len(ref1) == len(ref2):
		if len(new) != len(ref1):
			differences.append((path, "length", len(ref1), len(new)))
		for i, (n, r1, r2) in enumerate(zip(new, ref1, ref2)):
			compare(n, r1, r2, "%s[%d]" % (path, i), differences)
		return differences

	if shape(new) != shape(ref1) and shape(new) != shape(ref2):
		differences.append((path, "shape", shape(ref1), shape(new)))
	return differences


# Steps returning results of stochastic simulations, which can't be compared value by value
PROBABILITIES = ("simulation last_states/", "simulation states_trajs/", "simulation nodes_trajs/")
STOCHASTIC = (
	"simulation fixed_points/", "simulation observed_graph/", "simulation pca", "simulation sspca", "sensitivity steady states"
)
# Lists built from sets on the server, whose order changes when the server restarts
UNORDERED = {"graph_raw": ["edges"]}


def compare_probabilities(new, ref, tolerance, path="", differences=None):
	""" Probabilities must be within tolerance, and states only seen in one run must be unlikely """
	if isinstance(ref, dict) and isinstance(new, dict):
		for key in ref.keys() | new.keys():
			if key not in new or key not in ref:
				present = ref.get(key, new.get(key))
				if max_number(present) > tolerance:
					differences.append(("%s/%s" % (path, key), "missing" if key not in new else "unexpected", present, None))
			else:
				compare_probabilities(new[key], ref[key], tolerance, "%s/%s" % (path, key), differences)
	elif isinstance(ref, (int, float)) and isinstance(new, (int, float)) and not isinstance(ref, bool):
		if abs(new - ref) > tolerance:
			differences.append((path, "probability", ref, new))
	elif not equal(new, ref):
		differences.append((path, "value", ref, new))
	return differences


def max_number(value):
	if isinstance(value, dict):
		return max([max_number(v) for v in value.values()] + [0])
	if isinstance(value, list):
		return max([max_number(v) for v in value] + [0])
	if isinstance(value, (int, float)) and not isinstance(value, bool):
		return abs(value)
	return 0


def sort_unordered(step, record):
	for suffix, keys in UNORDERED.items():
		if step.endswith(suffix) and isinstance(record["body"], dict):
			record = dict(record, body=dict(record["body"]))
			for key in keys:
				if isinstance(record["body"].get(key), list):
					record["body"][key] = sorted(record["body"][key], key=json.dumps)
	return record


def compare_step(step, new, ref1, ref2, differences):
	new, ref1, ref2 = (sort_unordered(step, record) for record in (new, ref1, ref2))
	if step.endswith(PROBABILITIES):
		if new["status"] != ref1["status"]:
			differences.append((step, "status", ref1["status"], new["status"]))
		else:
			compare_probabilities(new["body"], ref1["body"], 0.08, step, differences)
	elif step.endswith(STOCHASTIC):
		# Only the structure of the response
		expected = (ref1["status"], sorted(ref1["body"]) if isinstance(ref1["body"], dict) else type(ref1["body"]).__name__)
		found = (new["status"], sorted(new["body"]) if isinstance(new["body"], dict) else type(new["body"]).__name__)
		if expected != found:
			differences.append((step, "structure", expected, found))
	else:
		compare(new, ref1, ref2, step, differences)


def truncate(value, length=200):
	text = json.dumps(value)
	return text if len(text) <= length else text[:length] + "..."


def main():
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--url", help="base url of the WebMaBoSS instance")
	parser.add_argument("--load", help="compare an existing snapshot instead of running the scenario")
	parser.add_argument("--out", help="where to write the snapshot")
	parser.add_argument("--compare", nargs=2, metavar=("REF1", "REF2"), help="two reference snapshots to compare with")
	parser.add_argument("--timeout", type=int, default=300, help="max seconds to wait for a simulation")
	args = parser.parse_args()

	smoke = Smoke(args.url or "", args.timeout)
	if args.load:
		with open(args.load) as f:
			snapshot = json.load(f)
	elif args.url:
		smoke.run()
		snapshot = smoke.snapshot()
	else:
		parser.error("--url or --load is required")

	if args.out:
		with open(args.out, "w") as f:
			json.dump(snapshot, f, indent=1, sort_keys=True)

	print("%d steps, %d failures" % (len(snapshot), len(smoke.failures)))
	for failure in smoke.failures:
		print("FAILURE  " + failure)

	differences = []
	if args.compare:
		refs = []
		for path in args.compare:
			with open(path) as f:
				refs.append(json.load(f))
		for step in sorted(set(refs[0]) | set(snapshot)):
			if step not in snapshot:
				differences.append((step, "missing step", None, None))
			elif step not in refs[0]:
				differences.append((step, "new step", None, None))
			elif step in refs[1]:
				compare_step(step, snapshot[step], refs[0][step], refs[1][step], differences)
		print("%d differences with the reference" % len(differences))
		for path, kind, expected, found in differences:
			print("DIFF  %s  [%s]\n      expected %s\n      found    %s" % (path, kind, truncate(expected), truncate(found)))

	sys.exit(1 if smoke.failures or differences else 0)


if __name__ == "__main__":
	main()
