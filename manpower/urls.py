from django.contrib import admin
from django.urls import path, include

import manpower.views as manpower_views
import manpower.user_manager
from manpower.department_manager import department_request
from manpower.user_manager import request_handler,add_user_from_file,add_simple_user,user_existance_checker
from manpower.ip_handler import ip_request_handler

urlpatterns = [
	path('',manpower_views.homepage, name='manpower_hompage'),
	path('department/', department_request,name='manage_manpower'),
	path('department/<action>', department_request,name='manage_manpower'),
	path('department/<action>/<id>', department_request,name='manage_manpower'),

	path('user/', request_handler,name='user_request_handler'),
	path('user/upload', add_user_from_file,name='add_user_from_file'),
	path('user/simple_upload', add_simple_user,name='add_simple_user'),
	path('user/user_check', user_existance_checker,name='user_existance_check'),
	path('user/<action>', request_handler,name='user_request_handler'),
	path('user/<action>/<query_string>', request_handler,name='user_request_handler'),
	path('ip/<action>',ip_request_handler,name='ip_request_handler'),

]