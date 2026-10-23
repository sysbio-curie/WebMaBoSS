#!/usr/bin/env python3
"""
Smoke test of the WebMaBoSS web interface, in a real browser.

It visits every page of the interface, anonymously and logged in, on a model
with a finished simulation and sensitivity analysis, and records for each page :
- the javascript errors (uncaught exceptions and console errors),
- the API requests which failed,
- a signature of what is displayed (headings, buttons, charts, tables...),
- a screenshot.

Like api_smoke.py, signatures taken on a reference version are compared with
those of an upgraded version. Screenshots are kept to compare them by eye.

    browser_smoke.py --url http://reference:8000 --out ref.json --screenshots ref/
    browser_smoke.py --url http://new:8000 --out new.json --screenshots new/ --compare ref.json

It runs in the image built from Dockerfile.browser.
"""

import argparse
import json
import os
import re
import sys
import time
import uuid

import requests
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# Default model, in the MaBoSS format of most stored models, with initial states like "Metastasis.istate = FALSE;"
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "api", "defaults", "models", "metastasis", "metastasis")

ANONYMOUS_PAGES = ["/", "/about/", "/tutorials/", "/tutorials/cohen/", "/tutorials/corral/", "/tutorials/sizek/", "/models/", "/login/", "/register/"]
USER_PAGES = ["/", "/models/", "/model/overview/", "/model/maboss/editing/", "/model/maboss/simulation/",
			  "/model/maboss/sensitivity/", "/model/fixed_points/", "/profile/account/", "/profile/maboss/", "/data/"]

# Errors which are expected, and not worth reporting
IGNORED_FAILED_REQUESTS = [
	("anonymous", r"/api/auth/is_logged_in$", 401),
]

# Console errors due to the tests, which reach the server over http with a hostname other than localhost.
# Django >= 4 sends a Cross-Origin-Opener-Policy header, which browsers only apply over https.
IGNORED_CONSOLE_ERRORS = [
	r"^The Cross-Origin-Opener-Policy header has been ignored, because the URL's origin was untrustworthy",
	# React 18.3 warns about what React 19 removes, here in libraries (reactstrap 8, react-fontawesome 0.1, the
	# transitions of reactstrap). To remove before React 19, and as soon as the libraries don't need them anymore
	r"^Warning: %s: Support for defaultProps will be removed from function components",
	r"^Warning: findDOMNode is deprecated and will be removed",
]


class Prepared:
	""" User, project, model, simulation and sensitivity analysis, created through the API """

	def __init__(self, url):
		self.url = url
		self.session = requests.Session()
		self.username = "smoke_" + uuid.uuid4().hex[:10]
		self.password = "Smoke-" + uuid.uuid4().hex

		response = self.api("post", "/api/auth/register", data={
			"username": self.username, "email": self.username + "@example.org",
			"password1": self.password, "password2": self.password,
		})
		self.session.headers["Authorization"] = "Token " + response.json()["key"]

		self.project = self.api("get", "/api/projects/").json()[0]["id"]
		with open(MODEL + ".bnd", "rb") as bnd, open(MODEL + ".cfg", "rb") as cfg:
			self.api("post", "/api/logical_models/%d/" % self.project, data={"name": "Metastasis"},
				files={"file": ("metastasis.bnd", bnd), "file2": ("metastasis.cfg", cfg)})
		# New projects also contain copies of the demo models
		models = self.api("get", "/api/logical_models/%d/" % self.project).json()
		self.model = [m["id"] for m in models if m["name"] == "Metastasis"][0]

		model = "/api/logical_model/%d/%d" % (self.project, self.model)
		defaults = self.api("get", model + "/maboss/settings/").json()
		outputs = defaults["output_variables"]
		settings = dict(defaults["settings"], sample_count=1000, max_time=10)
		self.api("post", model + "/maboss", data={
			"name": "smoke simulation", "settings": json.dumps(settings),
			"initialStates": json.dumps(defaults["initial_states"]),
			"outputVariables": json.dumps(defaults["output_variables"]),
			"observedGraphNodes": json.dumps({node: node in ["Migration", "Invasion", "Apoptosis"] for node in outputs}),
			"mutations": json.dumps({}),
		})
		simulation = self.api("get", model + "/maboss").json()[0]["id"]
		self.wait("/api/maboss/%d/%d/status" % (self.project, simulation), lambda s: s["done"])

		self.api("post", model + "/maboss_sensitivity", data={"settings": json.dumps({
			"name": "smoke sensitivity",
			"candidateVariables": {node: node in ["DNAdamage", "ECMicroenv"] for node in outputs},
			"outputVariables": outputs,
			"singleMutations": {"on": True, "off": True},
			"doubleMutations": {"on": False, "off": False},
		})})
		analysis = self.api("get", model + "/maboss_sensitivity").json()[0]["id"]
		self.wait("/api/maboss_sensitivity/%d/%d/status" % (self.project, analysis), lambda s: s["done"] == 1)

	def api(self, method, path, **kwargs):
		response = self.session.request(method, self.url + path, timeout=300, **kwargs)
		if response.status_code not in (200, 201):
			raise SystemExit("Preparation failed: %s %s returned %d" % (method, path, response.status_code))
		return response

	def wait(self, path, is_done, timeout=300):
		start = time.time()
		while time.time() - start < timeout:
			status = self.api("get", path).json()
			if status.get("failed"):
				raise SystemExit("Preparation failed: %s %s" % (path, status))
			if is_done(status):
				return
			time.sleep(1)
		raise SystemExit("Preparation failed: %s not finished" % path)

	def cleanup(self):
		self.api("delete", "/api/projects/%d" % self.project)


class Browser:

	def __init__(self, url, browser, screenshots):
		self.url = url
		self.browser = browser
		self.screenshots = screenshots
		self.records = {}
		self.errors = []

	def visit(self, page, who, path):
		self.record(page, who, "%s %s" % (who, path), lambda p: p.goto(self.url + path))

	def record(self, page, who, step, action):
		""" Runs an action (going to a page, clicking...), and records what happens and what is displayed """
		events = {"js_errors": [], "failed_requests": []}

		def on_console(message):
			if message.type == "error" and not any(re.search(p, message.text) for p in IGNORED_CONSOLE_ERRORS):
				events["js_errors"].append("console: " + message.text[:300])

		def on_page_error(error):
			events["js_errors"].append("exception: " + str(error)[:300])

		def on_response(response):
			url = response.url.replace(self.url, "")
			if response.status >= 400 and not any(
				who == w and re.search(p, url) and response.status == s for w, p, s in IGNORED_FAILED_REQUESTS
			):
				events["failed_requests"].append("%d %s" % (response.status, re.sub(r"/\d+", "/<id>", url)))

		page.on("console", on_console)
		page.on("pageerror", on_page_error)
		page.on("response", on_response)
		try:
			try:
				action(page)
			except PlaywrightError as e:
				# A button or a tab which is missing : recorded, and the next steps still run
				events["action_error"] = str(e).splitlines()[0][:300]
				self.errors.append("%s: %s" % (step, events["action_error"]))
				page.keyboard.press("Escape")
			page.wait_for_load_state("networkidle")
			# Charts and lazy loaded components
			page.wait_for_timeout(1500)
			page.wait_for_load_state("networkidle")

			record = {"url": page.url.replace(self.url, ""), "title": page.title()}
			record.update(page.evaluate(SIGNATURE))
			record.update(events)
			self.records[step] = record

			if self.screenshots:
				os.makedirs(self.screenshots, exist_ok=True)
				filename = re.sub(r"[^a-z0-9]+", "_", step.lower()).strip("_") + ".png"
				page.screenshot(path=os.path.join(self.screenshots, filename), full_page=True)

			for error in events["js_errors"] + events["failed_requests"]:
				self.errors.append("%s: %s" % (step, error))

		finally:
			page.remove_listener("console", on_console)
			page.remove_listener("pageerror", on_page_error)
			page.remove_listener("response", on_response)

	def run(self, prepared):
		context = self.browser.new_context(viewport={"width": 1400, "height": 900})
		page = context.new_page()

		for path in ANONYMOUS_PAGES:
			self.visit(page, "anonymous", path)

		# Logging in through the form
		page.goto(self.url + "/login/")
		page.fill("#username", prepared.username)
		page.fill("#password", prepared.password)
		page.click("#submit_login")
		page.wait_for_url(self.url + "/")
		self.records["login"] = {
			"url": page.url.replace(self.url, ""),
			"api_key_set": page.evaluate("window.sessionStorage.getItem('api_key') !== null"),
		}
		if not self.records["login"]["api_key_set"]:
			self.errors.append("login: no api key in the session storage")

		# Selecting the prepared model, as the models page does
		page.evaluate("([project, model]) => { sessionStorage.setItem('project', project); sessionStorage.setItem('model', model); }",
			[prepared.project, prepared.model])

		for path in USER_PAGES:
			self.visit(page, "user", path)
			for name, action in ACTIONS.get(path, []):
				self.record(page, "user", "user %s %s" % (path, name), action)

		self.visit(page, "user", "/logout/")
		self.records["logout"] = {
			"api_key_set": page.evaluate("window.sessionStorage.getItem('api_key') !== null"),
		}
		context.close()


def load_from_modal(button, item):
	""" Opens one of the 'Load existing ...' modals, and selects an item in its dropdown """
	def action(page):
		page.get_by_role("button", name=button).click()
		modal = page.locator(".modal.show")
		modal.locator(".dropdown-toggle").click()
		modal.get_by_text(item, exact=True).click()
		modal.get_by_role("button", name="Submit").click()
	return action


def open_tab(name):
	return lambda page: page.locator(".nav-link", has_text=name).click()


def open_new_simulation_tab(name):
	def action(page):
		page.get_by_role("button", name="New simulation").click()
		page.locator(".modal.show .nav-link", has_text=name).click()
	return action


def close_modal(page):
	page.keyboard.press("Escape")
	page.locator(".modal.show").wait_for(state="hidden")


def restore_demo_models(page):
	page.get_by_role("button", name="Restore demo models").click()
	page.locator(".modal.show").get_by_role("button", name="Yes").click()
	page.locator(".modal.show").wait_for(state="hidden")


# Interactions done on a page after loading it
ACTIONS = {
	"/models/": [
		("restore demo models", restore_demo_models),
	],
	"/model/maboss/editing/": [
		("tab Initial values", open_tab("Initial values")),
	],
	"/model/maboss/simulation/": [
		("new simulation Initial states", open_new_simulation_tab("Initial states")),
		("new simulation closed", close_modal),
		("new simulation Observed graph", open_new_simulation_tab("Observed graph")),
		("new simulation Observed graph closed", close_modal),
		("load simulation", load_from_modal("Load old simulation", "smoke simulation")),
	] + [
		("tab " + tab, open_tab(tab)) for tab in [
			"Nodes probability trajectories", "States probability trajectories", "Fixed points", "Observed graph",
			"Final state distribution"
		]
	],
	"/model/maboss/sensitivity/": [
		("load analysis", load_from_modal("Existing sensitivity analysis", "smoke sensitivity")),
	],
}


# What is displayed on the page, independently of the data
SIGNATURE = """() => {
	const visible = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
	const texts = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible)
		.map(e => e.innerText.trim().replace(/\\s+/g, ' ')).filter(t => t.length > 0 && t.length < 80);
	const count = (selector) => Array.from(document.querySelectorAll(selector)).filter(visible).length;
	return {
		headings: texts('h1, h2, h3, h4, h5, h6'),
		navigation: texts('nav a, .nav-link, .navbar-brand'),
		buttons: texts('button, .btn, input[type=submit]'),
		labels: texts('label'),
		// "NaN" displayed, or in a field : a value the interface could not read
		nan: (document.body.innerText.match(/\bNaN\b/g) || []).length
			+ Array.from(document.querySelectorAll('input')).filter(i => i.value === 'NaN').length,
		counts: {
			// Probabilities displayed : the interface shows nothing for values it can't read
			percentages: (document.body.innerText.match(/\d+(\.\d+)?\s*%/g) || []).length,
			charts: Array.from(document.querySelectorAll('canvas')).filter(c => visible(c) && c.width > 0).length,
			tables: count('table'),
			inputs: count('input, select, textarea'),
			images: count('img, svg'),
			modals: count('.modal.show'),
		},
	};
}"""


def compare(new, ref):
	differences = []
	for step in sorted(set(ref) | set(new)):
		if step not in new or step not in ref:
			differences.append((step, "missing" if step not in new else "new", None, None))
			continue
		for key in sorted(set(ref[step]) | set(new[step])):
			if new[step].get(key) != ref[step].get(key):
				differences.append((step, key, ref[step].get(key), new[step].get(key)))
	return differences


def main():
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--url", required=True, help="base url of the WebMaBoSS instance")
	parser.add_argument("--out", help="where to write the snapshot")
	parser.add_argument("--screenshots", help="directory where to save screenshots")
	parser.add_argument("--compare", help="reference snapshot to compare with")
	parser.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit"])
	args = parser.parse_args()

	url = args.url.rstrip("/")
	prepared = Prepared(url)

	with sync_playwright() as playwright:
		browser = getattr(playwright, args.browser).launch()
		smoke = Browser(url, browser, args.screenshots)
		try:
			smoke.run(prepared)
		finally:
			browser.close()
			prepared.cleanup()

	snapshot = json.loads(json.dumps(smoke.records).replace(prepared.username, "<username>"))
	if args.out:
		with open(args.out, "w") as f:
			json.dump(snapshot, f, indent=1, sort_keys=True)

	print("%d pages, %d errors" % (len(snapshot), len(smoke.errors)))
	for error in smoke.errors:
		print("ERROR  " + error)

	differences = []
	if args.compare:
		with open(args.compare) as f:
			differences = compare(snapshot, json.load(f))
		print("%d differences with the reference" % len(differences))
		for step, key, expected, found in differences:
			print("DIFF  %s  [%s]\n      expected %s\n      found    %s" % (step, key, json.dumps(expected), json.dumps(found)))

	sys.exit(1 if differences else 0)


if __name__ == "__main__":
	main()
