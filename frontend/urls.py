from django.urls import path, re_path
from . import views

urlpatterns = [
	# path('', views.index, name="home"),
	re_path('.*', views.index, name="home"),
]
