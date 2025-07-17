"""
URL configuration for operational_management_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import manpower.user_manager
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from manpower.api_handler import handle_api_request, user_login_api
import task_management.views
from task_management.report_handler import *
import task_management.russian_manager
import task_management.consultant_manager
from system_log import views
from system_log.group_sms import handle_sms_request
import task_management.feedback_manager as feedback
import system_log.notification_manager as notif_man
from task_management.doc_request_manager import document_request_handler
from task_management.lecture_manager import lecture_request_handler
urlpatterns = [
    path('admin_site_control/', admin.site.urls),
    path('ts/',include("technical_solution.urls")),
    path('',task_management.views.homepage,name='homepage'),
    path('ru_task/', task_management.russian_manager.ru_task_list, name='ru_task_list'),
    path('ru_discussion/', task_management.russian_manager.ru_discussion, name='ru_discussion'),
    path('ru_discussion/open/<id>', task_management.russian_manager.ru_open_discussion, name='ru_open_discussion'),
    path('consultant/', task_management.consultant_manager.consultant_request_handler, name='consultant'),
    path('consultant/<menu>', task_management.consultant_manager.consultant_request_handler, name='consultant'),
    path('consultant/<menu>/<action>', task_management.consultant_manager.consultant_request_handler, name='consultant'),
    path('consultant/<menu>/<action>/<id>', task_management.consultant_manager.consultant_request_handler, name='consultant'),
    path('task_management/', include('task_management.urls')),
    path('manpower/', include('manpower.urls')),
    path('system_log/', include('system_log.urls')),
    path('login/',manpower.user_manager.user_login,name='userlogin'),
    path('logout/',manpower.user_manager.logout_user,name='userlogout'),
    path('signup/',manpower.user_manager.signup,name='signup'),
    path('api/login',user_login_api,name='login_api'),
    path('api/<action>',handle_api_request,name='api'),
    path('group_sms/',handle_sms_request,name='group_sms'),
    path('feedback/<action>/',feedback.feedback_handler,name='feedback_handler'),
    path('feedback/<action>/<id>',feedback.feedback_handler,name='feedback_handler'),
    path('notifications/',notif_man.notification_handler,name='notification_handler'),
    path('notifications/<action>',notif_man.notification_handler,name='notification_handler'),
    path('notifications/<action>/<id>',notif_man.notification_handler,name='notification_handler'),
    path('document_request/<action>/',document_request_handler, name='document_request_handler'),
    path('document_request/<action>/<task_id>/',document_request_handler, name='document_request_handler'),
    path('document_request/<action>/<task_id>/<doc_request_id>',document_request_handler, name='document_request_handler'),
    path('lecture/',lecture_request_handler,name='lecture_request_handler'),
    path('lecture/<action>',lecture_request_handler,name='lecture_request_handler'),
    path('lecture/<action>/<id>',lecture_request_handler,name='lecture_request_handler'),
    path('report/', task_management.report_handler.report, name='report_handler'),
    path('report/<action>', task_management.report_handler.report, name='report_handler'),
    path('report/<action>/<id>', task_management.report_handler.report, name='report_handler'),
]
