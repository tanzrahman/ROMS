from django.contrib import admin
from django.urls import path, include
from system_log.views import *
import system_log.views as system_log

urlpatterns = [
	path('', system_log.homepage, name='system_log_homepage'),
	path('<action>', system_log.log_handler, name='log_handler'),
]