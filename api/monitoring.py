"""
Usage of WebMaBoSS, for its administrators : activity of the users, space used on disk and in the database, and
cleanup of what takes space.
"""

from collections import defaultdict
from datetime import timedelta
from os import walk, lstat
from os.path import join, isdir
from shutil import disk_usage
from threading import Thread

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Max, Q, Sum, Value
from django.db.models.functions import Coalesce, Length
from django.utils import timezone

from api.models import (
	Project, LogicalModel, MaBoSSSimulation, MaBoSSSensitivityAnalysis, MaBoSSSensitivitySimulation, UserActivity
)
from api.models.common import GUEST_USERNAME
from api.models.maboss import simulation_folder, sensitivityanalysis_folder

# Fields of the simulations which hold their results, in the database
RESULTS = ("fptable", "nodes_probtraj", "states_probtraj", "fixpoints")
SIMULATION_RESULTS = RESULTS + ("observed_graph",)

# Simulations still queued or running after that long were interrupted (by a restart of the server)
STALLED_AFTER = timedelta(days=1)

# Demo simulations of anonymous users are kept that long
DEMO_KEPT = timedelta(days=1)

# Number of simulations or analyses deleted per request, so that a request never takes too long
CLEANUP_BATCH = 50


def folder_size(path):
	""" Size of the files in a folder, in bytes """
	size = 0
	if isdir(path):
		for root, _, files in walk(path):
			for name in files:
				try:
					size += lstat(join(root, name)).st_size
				except OSError:
					pass
	return size


def results_size(fields=RESULTS):
	""" Expression of the size of the results of a simulation, in the database """
	return sum((Coalesce(Length(field), 0) for field in fields), Value(0))


def registered_users():
	""" The users who registered : without the account shared by anonymous users """
	return User.objects.exclude(username=GUEST_USERNAME)


# -------------------------------------------------------------------------------------------------------------------
# Activity

def period_start(day, period):
	if period == "week":
		return day - timedelta(days=day.weekday())
	elif period == "month":
		return day.replace(day=1)
	return day


def next_period(day, period):
	if period == "week":
		return day + timedelta(days=7)
	elif period == "month":
		return (day.replace(day=28) + timedelta(days=4)).replace(day=1)
	return day + timedelta(days=1)


def activity(start, end, period):
	"""
	Number of active users and of new users, for each day, week or month between start and end (dates, included)
	"""
	periods = []
	day = period_start(start, period)
	while day <= end:
		periods.append(day)
		day = next_period(day, period)

	active = defaultdict(set)
	for user_id, day in UserActivity.objects.filter(
		day__gte=periods[0] if periods else start, day__lte=end, user__in=registered_users()
	).values_list("user_id", "day"):
		active[period_start(day, period)].add(user_id)

	registered = defaultdict(int)
	for date_joined in registered_users().filter(
		date_joined__date__gte=periods[0] if periods else start, date_joined__date__lte=end
	).values_list("date_joined", flat=True):
		registered[period_start(timezone.localdate(date_joined), period)] += 1

	return {
		"period": period,
		"periods": [day.isoformat() for day in periods],
		"active": [len(active[day]) for day in periods],
		"registered": [registered[day] for day in periods],
	}


# -------------------------------------------------------------------------------------------------------------------
# Storage

def database_tables():
	""" Size of the tables of the database, in bytes, biggest first. Only for MySQL / MariaDB """
	if connection.vendor != "mysql":
		return []

	with connection.cursor() as cursor:
		cursor.execute(
			"SELECT table_name, table_rows, data_length + index_length, data_free FROM information_schema.tables "
			"WHERE table_schema = DATABASE() ORDER BY data_length + index_length DESC"
		)
		return [
			{"name": name, "rows": rows or 0, "size": int(size or 0), "free": int(free or 0)}
			for name, rows, size, free in cursor.fetchall()
		]


def storage():
	""" Space used by the data (files of the models and simulations) and by the database """
	tables = database_tables()
	projects = sum(folder_size(join(settings.MEDIA_ROOT, path)) for path in Project.objects.values_list("path", flat=True))
	total = folder_size(settings.MEDIA_ROOT)
	disk = disk_usage(settings.MEDIA_ROOT)

	return {
		"data": {"size": total, "projects": projects, "other": total - projects},
		"database": {
			"size": sum(table["size"] for table in tables),
			"free": sum(table["free"] for table in tables),
			"tables": tables,
		},
		"disk": {"size": disk.total, "free": disk.free},
	}


def users():
	""" The registered users, with their activity and the space they use """

	data = defaultdict(int)
	for user_id, path in Project.objects.values_list("user_id", "path"):
		data[user_id] += folder_size(join(settings.MEDIA_ROOT, path))

	database = defaultdict(int)
	for row in MaBoSSSimulation.objects.values("project__user").annotate(size=Sum(results_size(SIMULATION_RESULTS))):
		database[row["project__user"]] += row["size"] or 0
	for row in MaBoSSSensitivitySimulation.objects.values("sensitivity_analysis__project__user").annotate(
		size=Sum(results_size())
	):
		database[row["sensitivity_analysis__project__user"]] += row["size"] or 0

	def counts(model, field):
		return dict(model.objects.values_list(field).annotate(n=Count("id")))

	projects = counts(Project, "user")
	models = counts(LogicalModel, "project__user")
	simulations = counts(MaBoSSSimulation, "project__user")
	analyses = counts(MaBoSSSensitivityAnalysis, "project__user")

	return [
		{
			"id": user.id,
			"username": user.username,
			"email": user.email,
			"is_staff": user.is_staff,
			"date_joined": user.date_joined.isoformat(),
			"last_activity": user.last_activity.isoformat() if user.last_activity is not None else None,
			"projects": projects.get(user.id, 0),
			"models": models.get(user.id, 0),
			"simulations": simulations.get(user.id, 0),
			"analyses": analyses.get(user.id, 0),
			"data": data[user.id],
			"database": database[user.id],
		}
		for user in registered_users().annotate(last_activity=Max("activity__day")).order_by("id")
	]


def optimize_tables():
	"""
	Gives the free space of the tables back to the disk, in the background : MariaDB keeps the space of the rows
	which are deleted, and rebuilding a big table takes a while.
	"""
	if connection.vendor != "mysql":
		return []

	names = [table["name"] for table in database_tables() if table["free"] > 0]

	def optimize():
		try:
			with connection.cursor() as cursor:
				for name in names:
					cursor.execute("OPTIMIZE TABLE `%s`" % name.replace("`", ""))
					cursor.fetchall()
		finally:
			connection.close()

	Thread(target=optimize, daemon=True).start()
	return names


# -------------------------------------------------------------------------------------------------------------------
# Cleanup

CLEANUP_KINDS = ("old", "failed", "demo", "accounts")


def inactive_users(since):
	""" Registered users, not administrators, without activity since a date """
	return registered_users().filter(is_staff=False, is_superuser=False).exclude(
		activity__day__gte=since
	).exclude(date_joined__date__gte=since)


def cleanup_targets(kind, days=None, inactive_only=False):
	"""
	What a cleanup would delete : (simulations, analyses, users) querysets

	old : simulations and analyses created more than days ago, only those of users inactive since then if inactive_only
	failed : simulations which failed or were interrupted, analyses of which no simulation finished
	demo : simulations and analyses of the anonymous users, older than a day
	accounts : users inactive for more than days, with everything they have
	"""
	now = timezone.now()
	simulations = MaBoSSSimulation.objects.none()
	analyses = MaBoSSSensitivityAnalysis.objects.none()
	accounts = User.objects.none()

	if kind == "old":
		before = now - timedelta(days=days)
		simulations = MaBoSSSimulation.objects.filter(created_at__lt=before)
		analyses = MaBoSSSensitivityAnalysis.objects.filter(created_at__lt=before)
		if inactive_only:
			users = inactive_users(before.date())
			simulations = simulations.filter(project__user__in=users)
			analyses = analyses.filter(project__user__in=users)

	elif kind == "failed":
		stalled = now - STALLED_AFTER
		simulations = MaBoSSSimulation.objects.filter(
			Q(status__in=(MaBoSSSimulation.ERROR, MaBoSSSimulation.INTERRUPTED))
			| Q(status__in=(MaBoSSSimulation.QUEUED, MaBoSSSimulation.BUSY), created_at__lt=stalled)
		)
		analyses = MaBoSSSensitivityAnalysis.objects.filter(created_at__lt=stalled).annotate(
			finished=Count("mabosssensitivitysimulation", filter=Q(mabosssensitivitysimulation__status=MaBoSSSensitivitySimulation.ENDED))
		).filter(finished=0)

	elif kind == "demo":
		before = now - DEMO_KEPT
		simulations = MaBoSSSimulation.objects.filter(project__user__username=GUEST_USERNAME, created_at__lt=before)
		analyses = MaBoSSSensitivityAnalysis.objects.filter(project__user__username=GUEST_USERNAME, created_at__lt=before)

	elif kind == "accounts":
		accounts = inactive_users((now - timedelta(days=days)).date())
		simulations = MaBoSSSimulation.objects.filter(project__user__in=accounts)
		analyses = MaBoSSSensitivityAnalysis.objects.filter(project__user__in=accounts)

	else:
		raise ValueError("Unknown cleanup : %s" % kind)

	return simulations, analyses, accounts


def cleanup_preview(kind, days=None, inactive_only=False, max_items=100):
	""" What a cleanup would delete, and the space it would free """
	simulations, analyses, accounts = cleanup_targets(kind, days, inactive_only)

	simulations = simulations.select_related("project__user", "model").only(
		"id", "name", "path", "created_at", "status", "project__path", "project__user__username", "model__name"
	)
	analyses = analyses.select_related("project__user", "model").only(
		"id", "name", "path", "created_at", "project__path", "project__user__username", "model__name"
	)

	database = (
		(simulations.aggregate(size=Sum(results_size(SIMULATION_RESULTS)))["size"] or 0)
		+ (MaBoSSSensitivitySimulation.objects.filter(sensitivity_analysis__in=analyses.values("id")).aggregate(
			size=Sum(results_size()))["size"] or 0)
	)
	data = (
		sum(folder_size(simulation_folder(simulation)) for simulation in simulations)
		+ sum(folder_size(sensitivityanalysis_folder(analysis)) for analysis in analyses)
		+ sum(folder_size(join(settings.MEDIA_ROOT, path)) for path in Project.objects.filter(user__in=accounts).values_list("path", flat=True))
	)

	def item(kind, obj):
		return {
			"type": kind, "id": obj.id, "name": obj.name, "model": obj.model.name,
			"user": obj.project.user.username, "created_at": obj.created_at.isoformat(),
		}

	items = [item("simulation", simulation) for simulation in simulations.order_by("created_at")[:max_items]]
	items += [item("analysis", analysis) for analysis in analyses.order_by("created_at")[:max_items]]

	return {
		"kind": kind,
		"simulations": simulations.count(),
		"analyses": analyses.count(),
		"accounts": [
			{"id": user.id, "username": user.username, "date_joined": user.date_joined.isoformat()}
			for user in accounts.order_by("username")
		],
		"database": database,
		"data": data,
		"items": items,
	}


def cleanup(kind, days=None, inactive_only=False, batch=CLEANUP_BATCH):
	"""
	Deletes a batch of what a cleanup targets. Returns the number of simulations, analyses and accounts deleted, and
	what is left : it is called again until nothing is left.
	"""
	simulations, analyses, accounts = cleanup_targets(kind, days, inactive_only)

	# Without the results (deferred) : deleting loads the objects, for the signals which delete their files
	deleted_simulations = 0
	for simulation in simulations.select_related("project").only("id", "path", "bnd_file", "cfg_file", "project__path")[:batch]:
		simulation.delete()
		deleted_simulations += 1

	deleted_analyses = 0
	for analysis in analyses.select_related("project").only("id", "path", "project__path")[:batch]:
		# The results of its simulations are deleted without being loaded (no signal on them)
		analysis.delete()
		deleted_analyses += 1

	# The accounts once they have nothing heavy left : deleting them loads what they have
	deleted_accounts = 0
	if deleted_simulations == 0 and deleted_analyses == 0:
		for user in accounts[:batch]:
			user.delete()
			deleted_accounts += 1

	simulations, analyses, accounts = cleanup_targets(kind, days, inactive_only)
	return {
		"deleted": {"simulations": deleted_simulations, "analyses": deleted_analyses, "accounts": deleted_accounts},
		"left": simulations.count() + analyses.count() + accounts.count(),
	}
