from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

class InstallStatus(APIView):
	
	authentication_classes = [] #disables authentication
	permission_classes = [] #disables permission
	
	def __init__(self, *args, **kwargs):
		APIView.__init__(self, *args, **kwargs)
		self.data = {}

	def post(self, request, *args, **kwargs):

		self.data.update({
			'status': settings.RUN_INSTALL
		})

		return Response(data=self.data, status=status.HTTP_200_OK)