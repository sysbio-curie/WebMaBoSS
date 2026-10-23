from datetime import date, timedelta

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from api import monitoring


class AdminView(APIView):
	""" Only for the administrators (staff) """
	permission_classes = (IsAdminUser,)


class MonitoringAccess(APIView):
	""" Tells the interface whether to show the monitoring page : to everyone, so that it's never an error """
	permission_classes = (AllowAny,)

	def get(self, request):
		return Response({"admin": request.user.is_staff})


class MonitoringActivity(AdminView):

	def get(self, request):
		today = timezone.localdate()
		try:
			end = date.fromisoformat(request.query_params.get("end", today.isoformat()))
			start = date.fromisoformat(request.query_params.get("start", (end - timedelta(days=365)).isoformat()))
		except ValueError:
			raise ValidationError("start and end must be dates : YYYY-MM-DD")

		period = request.query_params.get("period", "week")
		if period not in ("day", "week", "month"):
			raise ValidationError("period must be day, week or month")
		if start > end:
			raise ValidationError("start must be before end")
		if period == "day" and (end - start).days > 5 * 366:
			raise ValidationError("At most 5 years by day")

		return Response(monitoring.activity(start, end, period))


class MonitoringStorage(AdminView):

	def get(self, request):
		return Response(monitoring.storage())


class MonitoringOptimize(AdminView):
	""" Gives the free space of the database back to the disk, in the background """

	def post(self, request):
		return Response({"tables": monitoring.optimize_tables()})


class MonitoringUsers(AdminView):
	""" The statistics of the users, as last computed (by the maintenance job), and computing them again """

	def get(self, request):
		statistics = monitoring.users_statistics()
		# Never computed yet
		if statistics["users"] is None and not statistics["computing"]:
			monitoring.compute_users_statistics_in_background()
			statistics = monitoring.users_statistics()
		return Response(statistics)

	def post(self, request):
		monitoring.compute_users_statistics_in_background()
		return Response(monitoring.users_statistics())


class MonitoringCleanup(AdminView):
	"""
	GET : what a cleanup would delete, and the space it would free
	POST : deletes a batch of it, to call again until nothing is left
	"""

	@staticmethod
	def parameters(data):
		kind = data.get("kind")
		if kind not in monitoring.CLEANUP_KINDS:
			raise ValidationError("kind must be one of " + ", ".join(monitoring.CLEANUP_KINDS))

		days = None
		if kind in ("old", "accounts"):
			try:
				days = int(data.get("days", ""))
			except ValueError:
				raise ValidationError("days must be a number")
			if days < 1:
				raise ValidationError("days must be at least 1")

		inactive_only = str(data.get("inactive_only", "")).lower() in ("1", "true")
		return kind, days, inactive_only

	def get(self, request):
		return Response(monitoring.cleanup_preview(*self.parameters(request.query_params)))

	def post(self, request):
		return Response(monitoring.cleanup(*self.parameters(request.data)))
