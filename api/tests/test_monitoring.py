from datetime import datetime, timedelta, date
from json import loads
from os.path import isdir, join

from django.conf import settings

from django.contrib.auth.models import User
from django.core.cache import cache, caches
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import status

from api.models import (
	Project, LogicalModel, MaBoSSSimulation, MaBoSSSensitivityAnalysis, MaBoSSSensitivitySimulation, UserActivity,
	ModelImport
)
from api.models.activity import estimate_past_activity
from api.models.common import create_guest_account
from api.models.maboss import simulation_folder, sensitivityanalysis_folder
from api.tests.APITestCase import APITestCase
from api.tests.test_simulate import SynchronousThread
from api.tests.test_repositories import FakeRepositories

from io import StringIO
import requests
from unittest.mock import patch


class TestMonitoring(APITestCase):

	fixtures = ['user.json']

	def setUp(self):
		APITestCase.setUp(self)
		cache.clear()
		caches["shared"].clear()
		# The statistics of the users are computed in a thread, which wouldn't see the test's database
		patcher = patch("api.monitoring.Thread", SynchronousThread)
		patcher.start()
		self.addCleanup(patcher.stop)
		self.admin = User.objects.get(username="admin")
		self.user = User.objects.create_user("user", "user@example.org", "user_password")

	def as_admin(self):
		self.client.force_authenticate(user=self.admin)

	def simulation(self, user, days_ago=0, status=MaBoSSSimulation.ENDED, results="x" * 1000):
		project = Project.objects.filter(user=user).first()
		simulation = MaBoSSSimulation(
			project=project, model=LogicalModel.objects.filter(project=project).first(), name="", status=status,
			nodes_probtraj=results,
			bnd_file=ContentFile(b"Node A { logic = A; }", name="model.bnd"),
			cfg_file=ContentFile(b"max_time = 1;", name="model.cfg"),
		)
		simulation.save()
		MaBoSSSimulation.objects.filter(id=simulation.id).update(created_at=timezone.now() - timedelta(days=days_ago))
		return simulation

	def analysis(self, user, days_ago=0, statuses=(MaBoSSSensitivitySimulation.ENDED,), results="y" * 1000):
		project = Project.objects.filter(user=user).first()
		analysis = MaBoSSSensitivityAnalysis(
			project=project, model=LogicalModel.objects.filter(project=project).first(), name="",
			bnd_file=ContentFile(b"Node A { logic = A; }", name="model.bnd"),
			cfg_file=ContentFile(b"max_time = 1;", name="model.cfg"),
		)
		analysis.save()
		for index, simulation_status in enumerate(statuses):
			MaBoSSSensitivitySimulation(
				sensitivity_analysis=analysis, name="sim %d" % index, status=simulation_status, nodes_probtraj=results
			).save()
		MaBoSSSensitivityAnalysis.objects.filter(id=analysis.id).update(created_at=timezone.now() - timedelta(days=days_ago))
		return analysis

	def run_cleanup(self, **parameters):
		""" Calls the cleanup until nothing is left, as the interface does """
		for _ in range(100):
			request = self.client.post('/api/monitoring/cleanup', parameters)
			self.assertEqual(request.status_code, status.HTTP_200_OK)
			if loads(request.content)["left"] == 0:
				return
		self.fail("The cleanup never ends")

	def testAccess(self):
		# Whether to show the page, to everyone
		self.assertEqual(loads(self.client.get('/api/monitoring/').content), {"admin": False})
		self.client.force_authenticate(user=self.user)
		self.assertEqual(loads(self.client.get('/api/monitoring/').content), {"admin": False})
		self.as_admin()
		self.assertEqual(loads(self.client.get('/api/monitoring/').content), {"admin": True})
		self.client.force_authenticate(user=None)

		paths = ['/api/monitoring/activity', '/api/monitoring/storage', '/api/monitoring/users',
				 '/api/monitoring/cleanup?kind=demo']

		# Anonymous users and users who are not administrators can't see it
		for path in paths:
			self.assertIn(self.client.get(path).status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
		self.client.force_authenticate(user=self.user)
		for path in paths:
			self.assertEqual(self.client.get(path).status_code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(self.client.post('/api/monitoring/cleanup', {"kind": "demo"}).status_code, status.HTTP_403_FORBIDDEN)

		self.as_admin()
		for path in paths:
			self.assertEqual(self.client.get(path).status_code, status.HTTP_200_OK)

	def testActivityRecorded(self):
		# Logging in, and using the API with the token, is recorded once a day
		request = self.client.post('/api/auth/login', {'username': 'user', 'password': 'user_password'})
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + loads(request.content)["key"])
		self.assertEqual(list(UserActivity.objects.filter(user=self.user).values_list("day", flat=True)), [timezone.localdate()])

		cache.clear()
		self.assertEqual(self.client.get('/api/projects/').status_code, status.HTTP_200_OK)
		self.assertEqual(self.client.get('/api/projects/').status_code, status.HTTP_200_OK)
		self.assertEqual(UserActivity.objects.filter(user=self.user).count(), 1)

		# Anonymous users are not recorded
		self.client.credentials()
		self.client.get('/api/projects/')
		self.assertEqual(UserActivity.objects.count(), 1)

	def testActivity(self):
		other = User.objects.create_user("other", "other@example.org", "other_password")
		User.objects.filter(id=other.id).update(date_joined=timezone.make_aware(datetime(2026, 3, 3, 12)))

		# Monday 2026-03-02 to Sunday 2026-03-08, and the next week
		for user, day in [(self.user, date(2026, 3, 2)), (self.user, date(2026, 3, 4)), (other, date(2026, 3, 4)),
						  (other, date(2026, 3, 10))]:
			UserActivity(user=user, day=day).save()
		create_guest_account()
		UserActivity(user=User.objects.get(username="____GUEST____"), day=date(2026, 3, 4)).save()

		self.as_admin()
		request = self.client.get('/api/monitoring/activity?start=2026-03-01&end=2026-03-14&period=week')
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		self.assertEqual(loads(request.content), {
			"period": "week",
			"periods": ["2026-02-23", "2026-03-02", "2026-03-09"],
			"active": [0, 2, 1],
			"registered": [0, 1, 0],
		})

		request = self.client.get('/api/monitoring/activity?start=2026-03-03&end=2026-03-04&period=day')
		self.assertEqual(loads(request.content)["active"], [0, 2])

		request = self.client.get('/api/monitoring/activity?start=2026-01-15&end=2026-03-31&period=month')
		self.assertEqual(loads(request.content)["periods"], ["2026-01-01", "2026-02-01", "2026-03-01"])
		self.assertEqual(loads(request.content)["active"], [0, 0, 2])

		for query in ['start=2026-03-14&end=2026-03-01', 'period=year', 'start=yesterday']:
			self.assertEqual(self.client.get('/api/monitoring/activity?' + query).status_code, status.HTTP_400_BAD_REQUEST)

	def testEstimatePastActivity(self):
		ignore_before = timezone.now() - timedelta(days=100)
		User.objects.filter(id=self.user.id).update(
			date_joined=timezone.now() - timedelta(days=200), last_login=timezone.now() - timedelta(days=50)
		)
		self.simulation(self.user, days_ago=20)
		self.simulation(self.user, days_ago=150)  # Before ignore_before : the date the column was added
		self.analysis(self.user, days_ago=10)

		UserActivity.objects.all().delete()
		estimate_past_activity(User, UserActivity, MaBoSSSimulation, MaBoSSSensitivityAnalysis, ignore_before)

		self.assertEqual(
			sorted(UserActivity.objects.filter(user=self.user).values_list("day", flat=True)),
			[(timezone.now() - timedelta(days=days)).date() for days in (200, 50, 20, 10)]
		)
		# Again, without duplicates
		estimate_past_activity(User, UserActivity, MaBoSSSimulation, MaBoSSSensitivityAnalysis, ignore_before)
		self.assertEqual(UserActivity.objects.filter(user=self.user).count(), 4)

	def testStorageAndUsers(self):
		self.simulation(self.user, results="x" * 1000)
		self.analysis(self.user, statuses=(MaBoSSSensitivitySimulation.ENDED,) * 2, results="y" * 500)
		UserActivity(user=self.user, day=date(2026, 3, 4)).save()
		create_guest_account()

		self.as_admin()
		request = self.client.get('/api/monitoring/storage')
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		storage = loads(request.content)
		self.assertGreater(storage["data"]["projects"], 0)
		self.assertEqual(storage["data"]["size"], storage["data"]["projects"] + storage["data"]["other"])
		self.assertGreater(storage["disk"]["size"], 0)
		self.assertIn("api_mabosssimulation", [table["name"] for table in storage["database"]["tables"]])

		# Computed on the first request, then kept
		request = self.client.get('/api/monitoring/users')
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		statistics = loads(request.content)
		self.assertFalse(statistics["computing"])
		self.assertIsNotNone(statistics["computed_at"])
		users = {user["username"]: user for user in statistics["users"]}
		self.assertEqual(sorted(users), ["admin", "user"])  # Without the account of anonymous users
		self.assertEqual(users["user"]["last_activity"], "2026-03-04")
		self.assertEqual(users["admin"]["last_activity"], None)
		self.assertEqual(
			(users["user"]["projects"], users["user"]["models"], users["user"]["simulations"], users["user"]["analyses"]),
			(1, LogicalModel.objects.filter(project__user=self.user).count(), 1, 1)
		)
		self.assertEqual(users["user"]["database"], 2000)
		self.assertGreater(users["user"]["data"], 0)
		self.assertTrue(users["admin"]["is_staff"])

	def testCleanupOld(self):
		User.objects.filter(id=self.user.id).update(date_joined=timezone.now() - timedelta(days=500))
		old = self.simulation(self.user, days_ago=400)
		recent = self.simulation(self.user, days_ago=10)
		old_analysis = self.analysis(self.user, days_ago=400)
		active = User.objects.create_user("active", "active@example.org", "active_password")
		active_old = self.simulation(active, days_ago=400)
		UserActivity(user=active, day=timezone.localdate()).save()
		self.assertTrue(isdir(simulation_folder(old)))
		self.assertTrue(isdir(sensitivityanalysis_folder(old_analysis)))

		self.as_admin()
		request = self.client.get('/api/monitoring/cleanup?kind=old&days=365')
		self.assertEqual(request.status_code, status.HTTP_200_OK)
		preview = loads(request.content)
		self.assertEqual((preview["simulations"], preview["analyses"]), (2, 1))
		self.assertEqual(preview["database"], 3000)
		self.assertGreater(preview["data"], 0)
		self.assertEqual(sorted(item["id"] for item in preview["items"] if item["type"] == "simulation"), [old.id, active_old.id])

		# Only for the users inactive since then
		preview = loads(self.client.get('/api/monitoring/cleanup?kind=old&days=365&inactive_only=true').content)
		self.assertEqual((preview["simulations"], preview["analyses"]), (1, 1))

		self.run_cleanup(kind="old", days=365, inactive_only="true")
		self.assertEqual(sorted(MaBoSSSimulation.objects.values_list("id", flat=True)), sorted([recent.id, active_old.id]))
		self.assertFalse(MaBoSSSensitivityAnalysis.objects.exists())
		self.assertFalse(MaBoSSSensitivitySimulation.objects.exists())
		self.assertFalse(isdir(simulation_folder(old)))
		self.assertFalse(isdir(sensitivityanalysis_folder(old_analysis)))

		self.run_cleanup(kind="old", days=365)
		self.assertEqual(list(MaBoSSSimulation.objects.values_list("id", flat=True)), [recent.id])

	def testCleanupFailed(self):
		failed = self.simulation(self.user, status=MaBoSSSimulation.ERROR)
		interrupted = self.simulation(self.user, days_ago=3, status=MaBoSSSimulation.BUSY)
		running = self.simulation(self.user, status=MaBoSSSimulation.BUSY)
		finished = self.simulation(self.user, days_ago=3)
		failed_analysis = self.analysis(self.user, days_ago=3, statuses=(MaBoSSSensitivitySimulation.ERROR, MaBoSSSensitivitySimulation.BUSY))
		empty_analysis = self.analysis(self.user, days_ago=3, statuses=())
		partial_analysis = self.analysis(self.user, days_ago=3, statuses=(MaBoSSSensitivitySimulation.ERROR, MaBoSSSensitivitySimulation.ENDED))
		running_analysis = self.analysis(self.user, statuses=(MaBoSSSensitivitySimulation.BUSY,))

		self.as_admin()
		preview = loads(self.client.get('/api/monitoring/cleanup?kind=failed').content)
		self.assertEqual((preview["simulations"], preview["analyses"]), (2, 2))

		self.run_cleanup(kind="failed")
		self.assertEqual(sorted(MaBoSSSimulation.objects.values_list("id", flat=True)), sorted([running.id, finished.id]))
		self.assertEqual(sorted(MaBoSSSensitivityAnalysis.objects.values_list("id", flat=True)), sorted([partial_analysis.id, running_analysis.id]))

	def testCleanupDemo(self):
		guest = create_guest_account()
		old = self.simulation(guest, days_ago=2)
		recent = self.simulation(guest)
		old_analysis = self.analysis(guest, days_ago=2)
		users = self.simulation(self.user, days_ago=2)
		demo_models = LogicalModel.objects.filter(project__user=guest).count()

		self.as_admin()
		preview = loads(self.client.get('/api/monitoring/cleanup?kind=demo').content)
		self.assertEqual((preview["simulations"], preview["analyses"]), (1, 1))
		self.assertEqual(preview["items"][0]["user"], "____GUEST____")

		self.run_cleanup(kind="demo")
		self.assertEqual(sorted(MaBoSSSimulation.objects.values_list("id", flat=True)), sorted([recent.id, users.id]))
		self.assertFalse(MaBoSSSensitivityAnalysis.objects.exists())
		# The demo models are kept
		self.assertEqual(LogicalModel.objects.filter(project__user=guest).count(), demo_models)

	def testCleanupAccounts(self):
		long_ago = timezone.now() - timedelta(days=800)
		inactive = User.objects.create_user("inactive", "inactive@example.org", "inactive_password")
		inactive_project = Project.objects.get(user=inactive)
		self.simulation(inactive, days_ago=800)
		self.analysis(inactive, days_ago=800)
		UserActivity(user=inactive, day=long_ago.date()).save()
		User.objects.filter(id__in=[inactive.id, self.admin.id, self.user.id]).update(date_joined=long_ago)
		UserActivity(user=self.user, day=timezone.localdate()).save()
		create_guest_account()
		User.objects.filter(username="____GUEST____").update(date_joined=long_ago)

		self.as_admin()
		preview = loads(self.client.get('/api/monitoring/cleanup?kind=accounts&days=730').content)
		# Not the administrators, the active users, nor the account of anonymous users
		self.assertEqual([account["username"] for account in preview["accounts"]], ["inactive"])
		self.assertEqual((preview["simulations"], preview["analyses"]), (1, 1))

		self.run_cleanup(kind="accounts", days=730)
		self.assertEqual(sorted(User.objects.values_list("username", flat=True)), ["____GUEST____", "admin", "user"])
		self.assertFalse(Project.objects.filter(id=inactive_project.id).exists())
		self.assertFalse(isdir(join(settings.MEDIA_ROOT, inactive_project.path)))

	def testCleanupParameters(self):
		self.as_admin()
		for parameters in [{}, {"kind": "everything"}, {"kind": "old"}, {"kind": "old", "days": "0"}, {"kind": "accounts", "days": "many"}]:
			self.assertEqual(self.client.post('/api/monitoring/cleanup', parameters).status_code, status.HTTP_400_BAD_REQUEST)


class TestMaintenance(APITestCase):
	""" manage.py maintenance """

	fixtures = TestMonitoring.fixtures
	setUp = TestMonitoring.setUp
	simulation = TestMonitoring.simulation

	def maintenance(self, *tasks):
		output = StringIO()
		call_command("maintenance", *(["--only"] + list(tasks) if tasks else []), stdout=output, stderr=output)
		return output.getvalue()

	def testDemoAndStalled(self):
		guest = create_guest_account()
		old_demo = self.simulation(guest, days_ago=2)
		new_demo = self.simulation(guest, days_ago=0)
		stalled = self.simulation(self.user, days_ago=2, status=MaBoSSSimulation.BUSY)
		running = self.simulation(self.user, days_ago=0, status=MaBoSSSimulation.BUSY)

		output = self.maintenance("demo", "stalled")
		self.assertIn("1 demo simulations and analyses deleted", output)
		self.assertEqual(
			sorted(MaBoSSSimulation.objects.values_list("id", flat=True)), sorted([new_demo.id, stalled.id, running.id])
		)
		self.assertEqual(MaBoSSSimulation.objects.get(id=stalled.id).status, MaBoSSSimulation.INTERRUPTED)
		self.assertEqual(MaBoSSSimulation.objects.get(id=running.id).status, MaBoSSSimulation.BUSY)

	def testImports(self):
		project = Project.objects.filter(user=self.user).first()
		stalled = ModelImport.objects.create(project=project, repository="ginsim", remote_id="a", name="a")
		running = ModelImport.objects.create(project=project, repository="ginsim", remote_id="b", name="b")
		old = ModelImport.objects.create(project=project, repository="ginsim", remote_id="c", name="c", status=ModelImport.ENDED)
		ModelImport.objects.filter(id=stalled.id).update(created_at=timezone.now() - timedelta(hours=2))
		ModelImport.objects.filter(id=old.id).update(updated_at=timezone.now() - timedelta(days=8))

		self.maintenance("imports")
		self.assertEqual(ModelImport.objects.get(id=stalled.id).status, ModelImport.ERROR)
		self.assertEqual(ModelImport.objects.get(id=running.id).status, ModelImport.BUSY)
		self.assertFalse(ModelImport.objects.filter(id=old.id).exists())

	def testStatisticsAndRepositories(self):
		self.simulation(self.user)
		with patch("api.repositories.requests.get", FakeRepositories().get):
			output = self.maintenance("users", "repositories", "sessions")
		self.assertIn("statistics of 2 users computed", output)
		self.assertIn("models listed : BioModels 1, Cell Collective 1, GINsim 3", output)

		# Shown without being computed again
		self.client.force_authenticate(user=self.admin)
		with patch("api.monitoring.users", side_effect=AssertionError("computed again")):
			statistics = loads(self.client.get('/api/monitoring/users').content)
		self.assertEqual(sorted(user["username"] for user in statistics["users"]), ["admin", "user"])

		# The repositories are listed from the cache
		with patch("api.repositories.requests.get", side_effect=AssertionError("listed again")):
			self.assertEqual(len(loads(self.client.get('/api/repositories/ginsim/').content)), 3)

	def testUnreachableRepository(self):
		def unreachable(url, **kwargs):
			raise requests.ConnectionError("unreachable")
		with patch("api.repositories.requests.get", unreachable):
			output = self.maintenance("repositories")
		# The other tasks would still run, and the command doesn't fail for it
		self.assertIn("BioModels unreachable (unreachable)", output)
