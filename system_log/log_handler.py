from django.shortcuts import render, redirect
from system_log.models import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from task_management.models import SystemParameter


def login_log(request, page_no=None):
    user_log = UserLog.objects.all().order_by('-time')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(user_log, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        user_log = paginator.page(page_no)

    except PageNotAnInteger:
        user_log = paginator.page(page_no)

    except EmptyPage:
        user_log = paginator.page(paginator.num_pages)

    context = {
                "user_log": user_log,
              }
    return render(request, 'system_log/login_log.html', context)

def password_change_log(request, page_no=None):
    log_list = PasswordChangeLog.objects.all().order_by('-time')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(log_list, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        log_list = paginator.page(page_no)
    except PageNotAnInteger:
        log_list = paginator.page(page_no)
    except EmptyPage:
        log_list = paginator.page(paginator.num_pages)

    return render(request, 'system_log/password_change_log.html', {'password_change_log': log_list})


def file_log(request, page_no=None):
    log_list = FileLog.objects.all().order_by('-time')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(log_list, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        log_list = paginator.page(page_no)
    except PageNotAnInteger:
        log_list = paginator.page(page_no)
    except EmptyPage:
        log_list = paginator.page(paginator.num_pages)

    return render(request, 'system_log/file_log.html', {'file_log': log_list})


def task_log(request, page_no=None):
    log_list = TaskLog.objects.all().order_by('-created_at')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(log_list, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        log_list = paginator.page(page_no)
    except PageNotAnInteger:
        log_list = paginator.page(page_no)
    except EmptyPage:
        log_list = paginator.page(paginator.num_pages)

    return render(request, 'system_log/task_log.html', {'task_log': log_list})


def failed_login_log(request, page_no=None):
    log_list = FailedLoginLog.objects.all().order_by('-time')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(log_list, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        log_list = paginator.page(page_no)
    except PageNotAnInteger:
        log_list = paginator.page(page_no)
    except EmptyPage:
        log_list = paginator.page(paginator.num_pages)

    return render(request, 'system_log/failed_login_log.html', {'failed_login_log': log_list})


def deactivated_user_log(request, page_no=None):
    log_list = UserDeactivateLog.objects.all().order_by('-time')

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # pagination number comes from system parameter model
    paginator_object = SystemParameter.objects.filter(name='pagination_number')
    no_of_items = 10
    if (paginator_object.count() != 0):
        no_of_items = paginator_object[0].value

    paginator = Paginator(log_list, no_of_items)

    if (not page_no):
        page_no = 1
    try:
        log_list = paginator.page(page_no)
    except PageNotAnInteger:
        log_list = paginator.page(page_no)
    except EmptyPage:
        log_list = paginator.page(paginator.num_pages)

    return render(request, 'system_log/deactivated_user_log.html', {'deactivated_user_log': log_list})