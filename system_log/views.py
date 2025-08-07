from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import Group, GroupManager, Permission
from django.http import HttpResponse, JsonResponse

from system_log.models import *
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from task_management.models import SystemParameter
from system_log.log_handler import *



def homepage(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')

    return render(request, 'system_log/system_log_base.html')


def log_handler(request,action="",id=""):
    if (request.user.is_anonymous):
        return redirect('/')

    if(action == 'login_log'):
        return login_log(request)
    if(action == 'password_change_log'):
        return password_change_log(request)
    if(action == 'file_log'):
        return file_log(request)
    if(action == 'task_log'):
        return task_log(request)
    if(action == 'failed_login_log'):
        return failed_login_log(request)
    if(action == 'deactivated_user_log'):
        return deactivated_user_log(request)
    else:
        return HttpResponse("Invalid Access")


