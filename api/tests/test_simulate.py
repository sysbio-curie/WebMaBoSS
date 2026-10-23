from django.conf import settings
from rest_framework import status

from api.tests.APITestCase import APITestCase
from api.models import LogicalModel, Project

from json import loads, dumps
from os.path import join, dirname, exists
from shutil import copytree, rmtree
from unittest.mock import patch


class TestSimulate(APITestCase):
	fixtures = ['models.json']

	def __init__(self, *args, **kwargs):
		APITestCase.__init__(self, *args, **kwargs)
		self.client = None
		self.projects = []

	def setUp(self):

		APITestCase.setUp(self)

		self.projects = Project.objects.all()
		for project in self.projects:
			if exists(join(dirname(__file__), 'fixtures', 'models', project.path)):
				copytree(
					join(dirname(__file__), 'fixtures', 'models', project.path),
					join(settings.MEDIA_ROOT, project.path)
				)

	def testSimulate(self):

		self.login()

		project = self.projects[1]
		model = LogicalModel.objects.filter(project=project)[0]

		request = self.client.get("/api/logical_model/%d/%d/maboss/settings/" % (project.id, model.id))
		self.assertEqual(request.status_code, status.HTTP_200_OK)

		settings = loads(request.content.decode())

		self.assertEqual(
			settings["output_variables"],
			{"ECMicroenv": False, "DNAdamage": False, "Metastasis": True, "Migration": True, "Invasion": True,
			 "EMT": False, "Apoptosis": True, "CellCycleArrest": True, "GF": False, "TGFbeta": False, "p21": False,
			 "CDH1": False, "CDH2": False, "VIM": False, "TWIST1": False, "SNAI1": False, "SNAI2": False, "ZEB1": False,
			 "ZEB2": False, "AKT1": False, "DKK1": False, "CTNNB1": False, "NICD": False, "p63": False, "p53": False,
			 "p73": False, "miR200": False, "miR203": False, "miR34": False, "AKT2": False, "ERK": False, "SMAD": False}
		)
		
		self.assertEqual(
			settings["initial_states"],
			{'ECMicroenv': {'0': 0.5, '1': 0.5}, 'DNAdamage': {'0': 0.5, '1': 0.5}, 
			 'Metastasis': {'0': 1.0, '1': 0.0}, 'Migration': {'0': 1.0, '1': 0.0}, 
			 'Invasion': {'0': 1.0, '1': 0.0}, 'EMT': {'0': 1.0, '1': 0.0}, 
			 'Apoptosis': {'0': 1.0, '1': 0.0}, 'CellCycleArrest': {'0': 1.0, '1': 0.0}, 
			 'GF': {'0': 1.0, '1': 0.0}, 'TGFbeta': {'0': 1.0, '1': 0.0}, 'p21': {'0': 1.0, '1': 0.0}, 
			 'CDH1': {'0': 1.0, '1': 0.0}, 'CDH2': {'0': 1.0, '1': 0.0}, 'VIM': {'0': 1.0, '1': 0.0}, 
			 'TWIST1': {'0': 1.0, '1': 0.0}, 'SNAI1': {'0': 1.0, '1': 0.0}, 'SNAI2': {'0': 1.0, '1': 0.0}, 
			 'ZEB1': {'0': 1.0, '1': 0.0}, 'ZEB2': {'0': 1.0, '1': 0.0}, 'AKT1': {'0': 1.0, '1': 0.0}, 
			 'DKK1': {'0': 1.0, '1': 0.0}, 'CTNNB1': {'0': 1.0, '1': 0.0}, 'NICD': {'0': 1.0, '1': 0.0}, 
			 'p63': {'0': 1.0, '1': 0.0}, 'p53': {'0': 1.0, '1': 0.0}, 'p73': {'0': 1.0, '1': 0.0}, 
			 'miR200': {'0': 1.0, '1': 0.0}, 'miR203': {'0': 1.0, '1': 0.0}, 'miR34': {'0': 1.0, '1': 0.0}, 
			 'AKT2': {'0': 1.0, '1': 0.0}, 'ERK': {'0': 1.0, '1': 0.0}, 'SMAD': {'0': 1.0, '1': 0.0}
			}
		)

		# request = self.client.post(
		# 	"/api/logical_model/%d/%d/maboss" % (project.id, model.id),
		# 	{
		# 		'name': 'test_sim',
		# 		'settings': dumps(settings["settings"]),
		# 		'initialStates': dumps(settings["initial_states"]),
		# 		'outputVariables': dumps(settings["output_variables"]),
		# 		'mutations': dumps(settings["mutations"])
		# 	}
		
		
			# dumps(settings)
		
		# )
		# self.assertEqual(request.status_code, status.HTTP_200_OK)
		# print(request.content)


class SynchronousThread:
	""" Runs the simulation in the test, instead of in a thread which wouldn't see the test's database """
	def __init__(self, target, args):
		self.target, self.args = target, args

	def start(self):
		self.target(*self.args)


class TestObservedGraph(APITestCase):
	fixtures = TestSimulate.fixtures
	setUp = TestSimulate.setUp

	def simulate(self, observed_nodes, **extra):
		project = self.projects[1]
		model = LogicalModel.objects.filter(project=project)[0]

		request = self.client.get("/api/logical_model/%d/%d/maboss/settings/" % (project.id, model.id))
		settings = loads(request.content.decode())
		self.assertEqual(set(settings["observed_graph_nodes"].values()), {False})

		settings["settings"].update({"sample_count": 200, "max_time": 20})
		observed_graph_nodes = {node: node in observed_nodes for node in settings["observed_graph_nodes"]}

		with patch("api.views.maboss.MaBoSSSimulationView.Thread", SynchronousThread):
			request = self.client.post(
				"/api/logical_model/%d/%d/maboss" % (project.id, model.id),
				dict({
					'name': 'test_observed_graph',
					'settings': dumps(settings["settings"]),
					'initialStates': dumps(settings["initial_states"]),
					'outputVariables': dumps(settings["output_variables"]),
					'observedGraphNodes': dumps(observed_graph_nodes),
					'mutations': dumps(settings["mutations"])
				}, **extra)
			)
		return project, request

	def testObservedGraph(self):

		self.login()
		project, request = self.simulate(["Apoptosis", "Migration", "EMT"])
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		simulation_id = loads(request.content.decode())["simulation_id"]

		request = self.client.get("/api/maboss/%d/%d/observed_graph/" % (project.id, simulation_id))
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		graph = loads(request.content.decode())["observed_graph"]

		self.assertEqual(set(graph["nodes"]), {"EMT", "Migration", "Apoptosis"})
		self.assertGreater(len(graph["edges"]), 0)
		for source, target, proba in graph["edges"]:
			self.assertIn(source, graph["states"])
			self.assertIn(target, graph["states"])
			self.assertTrue(0 < proba <= 1)

		# From each state left, the probabilities of the next ones add up to 1
		for state in set(edge[0] for edge in graph["edges"]):
			self.assertAlmostEqual(sum(edge[2] for edge in graph["edges"] if edge[0] == state), 1, places=4)

		# Kept in the cfg of the simulation, which can still be read (needs pyMaBoSS > 0.8.16)
		cfg = self.client.get("/api/maboss/%d/%d/cfg_file" % (project.id, simulation_id))
		cfg = b"".join(cfg.streaming_content).decode()
		self.assertIn("Apoptosis.in_graph = True;", cfg)
		self.assertNotIn("p53.in_graph", cfg)
		request = self.client.get("/api/maboss/%d/%d/sspca" % (project.id, simulation_id))
		self.assertEqual(request.status_code, status.HTTP_200_OK)

		# And in the model saved from the simulation, whose settings select them again
		request = self.client.get("/api/maboss/%d/%d/new_model" % (project.id, simulation_id))
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		new_model = LogicalModel.objects.filter(project=project).order_by("-id")[0]
		request = self.client.get("/api/logical_model/%d/%d/maboss/settings/" % (project.id, new_model.id))
		selected = loads(request.content.decode())["observed_graph_nodes"]
		self.assertEqual({node for node, value in selected.items() if value}, {"EMT", "Migration", "Apoptosis"})

	def testWithoutObservedGraph(self):

		self.login()
		project, request = self.simulate([])
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		simulation_id = loads(request.content.decode())["simulation_id"]

		request = self.client.get("/api/maboss/%d/%d/observed_graph/" % (project.id, simulation_id))
		self.assertIsNone(loads(request.content.decode())["observed_graph"])

	def testObservedGraphLimits(self):

		self.login()
		_, request = self.simulate(["EMT", "Migration", "Apoptosis", "p53", "p63", "p73", "ZEB1", "ZEB2", "SNAI1"])
		self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)

		# MaBoSS servers don't send it back
		_, request = self.simulate(["EMT"], serverHost="localhost", serverPort="7777")
		self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
