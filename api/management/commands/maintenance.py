from datetime import timedelta
import time
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from api import monitoring
from api.models import ModelImport
from api.models.common import clean_guest_account
from api.repositories import REPOSITORIES, RepositoryError, LIST_KEPT_BY_MAINTENANCE

# Imports still running after that long were interrupted (by a restart of the server)
IMPORT_STALLED_AFTER = timedelta(hours=1)
# Finished imports are kept that long, for the interface following them
IMPORTS_KEPT = timedelta(days=7)


def clean_demo():
	deleted = 0
	while True:
		result = clean_guest_account()
		deleted += sum(result["deleted"].values())
		if result["left"] == 0 or sum(result["deleted"].values()) == 0:
			return "%d demo simulations and analyses deleted" % deleted


def interrupt_stalled():
	return "%d stalled simulations and analyses marked as interrupted" % monitoring.interrupt_stalled()


def clean_imports():
	now = timezone.now()
	stalled = ModelImport.objects.filter(status=ModelImport.BUSY, created_at__lt=now - IMPORT_STALLED_AFTER).update(
		status=ModelImport.ERROR, error="The import was interrupted"
	)
	deleted, _ = ModelImport.objects.exclude(status=ModelImport.BUSY).filter(updated_at__lt=now - IMPORTS_KEPT).delete()
	return "%d stalled imports, %d old imports deleted" % (stalled, deleted)


def clear_sessions():
	call_command("clearsessions")
	return "expired sessions deleted"


def refresh_repositories():
	results = []
	for repository in REPOSITORIES.values():
		try:
			results.append("%s %d" % (repository.title, len(repository.refresh(LIST_KEPT_BY_MAINTENANCE))))
		except RepositoryError as e:
			# The previous list is still there
			results.append("%s unreachable (%s)" % (repository.title, e))
	return "models listed : " + ", ".join(results)


def compute_users():
	start = time.time()
	statistics = monitoring.compute_users_statistics()
	return "statistics of %d users computed in %.0fs" % (len(statistics["users"]), time.time() - start)


TASKS = {
	"demo": clean_demo,
	"stalled": interrupt_stalled,
	"imports": clean_imports,
	"sessions": clear_sessions,
	"repositories": refresh_repositories,
	"users": compute_users,
}


class Command(BaseCommand):
	help = (
		"Maintenance of WebMaBoSS : deletes the old simulations of the anonymous users, marks the simulations interrupted "
		"by a restart, cleans the imports and the expired sessions, lists the models of the repositories again and "
		"computes the statistics of the users. The container runs it every hour (maintenance.sh)."
	)

	def add_arguments(self, parser):
		parser.add_argument("--only", nargs="+", choices=sorted(TASKS), default=None, help="only these tasks")

	def run(self, tasks):
		failed = False
		for name in tasks:
			try:
				self.stdout.write("%s %s : %s" % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), name, TASKS[name]()))
			except Exception:
				# The other tasks still run, and this one will be tried again next time
				failed = True
				self.stderr.write("%s %s failed :\n%s" % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), name, traceback.format_exc()))
		return failed

	def handle(self, *args, **options):
		if self.run(options["only"] or list(TASKS)):
			raise SystemExit(1)
