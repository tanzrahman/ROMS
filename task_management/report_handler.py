import threading
import datetime
import json
from django.core import paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.models import *
from system_log.models import *
from task_management.notify_users import send_notification, send_notification_non_departmental
from task_management.system_list import systems as system_list
from task_management.forms import *
from task_management.models import *

def report(request, action=None, id=None):
    if (request.user.is_anonymous):
        return redirect('/')

    # if(action == 'consultant_task_feedback'):
    #     return consultant_task_feedback(request,action,id)
    # else:
    #     return HttpResponse("Invalid")

    if(action=="task_distribution"):
        return task_distribution_report(request)

    if (action == "consultant_tasks_report"):
        return consultant_task_report(request,action,id)

    if(action=="consultant_feedback"):
        return consultant_feedback_show(request, action, id)

    if(action=="consultant_discussion_feedback"):
        return consultant_discussion_feedback_show(request, action, id)

    if(action=="consultant_discussion_report"):
        return consultant_discussion_report(request, action)



    return render(request, 'consultant/consultant_task_report.html')


def consultant_task_report(request,action,id):
    total_feedback = ConsultantTasks.objects.all().order_by('-report_submitted_at')

    consultant_feedback_count = {}

    consultant = Profile.objects.filter(access_level=75)
    for each in consultant:
        consultant_feedback_count.update({
                each.user: [ConsultantTasks.objects.filter(consultant=each.user).exclude(review_report=None).count(),
                         ConsultantTasks.objects.filter(consultant=each.user).count()]
             })

    search_form = ConsultantTaskFeedbackSearchForm(request.GET)

    search_filters = []
    if (search_form.is_valid()):
        for each in search_form.changed_data:
            if (each == 'division'):
                search_filters.append(Q(**{'task__division': search_form.cleaned_data[each]}))
            elif (each == 'task'):
                search_filters.append(Q(**{'task': search_form.cleaned_data[each]}))
            elif (each == 'consultant'):
                search_filters.append(Q(**{'consultant': search_form.cleaned_data[each]}))
            elif (each == 'task_category'):
                search_filters.append(Q(**{'task__task_category': search_form.cleaned_data[each]}))
            elif (each == 'feedback_from'):
                search_filters.append(Q(**{'report_submitted_at__gte': search_form.cleaned_data[each]}))
            elif (each == 'feedback_to'):
                search_filters.append(Q(**{'report_submitted_at__lte': search_form.cleaned_data[each]}))

    if (len(search_filters) > 0):
        total_feedback = ConsultantTasks.objects.filter(reduce(operator.and_, search_filters)).order_by('-report_submitted_at')

    if(request.GET.get('filter')):
        if(request.GET.get('filter') != 'all'):
            total_feedback = total_feedback.exclude(review_report=None)

    context = {
        'form': search_form,
        'total_feedback': total_feedback,
        'consultant_feedback_count': consultant_feedback_count,
    }
    return render(request, 'consultant/consultant_task_report.html', context)


def consultant_feedback_show(request, action, id):
    print(id)
    feedback = ConsultantTasks.objects.get(id=id)
    print(feedback)
    comment_list = Comment.objects.filter(consultant_task_feedback=feedback).order_by('-created_date')
    context = {
        'feedback': feedback,
        'comment_list': comment_list,
    }

    return render(request, 'consultant/consultant_task_report_show.html', context)


def consultant_discussion_report(request, action):
    total_feedback = ConsultantQA.objects.all().order_by('-created_at')

    consultant_feedback_count = {}
    consultant = Profile.objects.filter(access_level=75)
    for each in consultant:
        consultant_feedback_count.update({
            each.user:
                [
                    ConsultantQA.objects.filter(consultant=each.user).count(),
                    ConsultantLecture.objects.filter(consultant=each.user,lecture__schedule__lte=datetime.datetime.now()).count(),
                    ConsultantLecture.objects.filter(consultant=each.user).count()
                ]
        })

    search_form = ConsultantLectureFeedbackSearchForm(request.GET)

    search_filters = []
    if(search_form.is_valid()):
        for each in search_form.changed_data:
            if(each == 'division'):
                search_filters.append(Q(**{'lecture__target_division': search_form.cleaned_data[each]}))
            # elif(each == 'task'):
            #     search_filters.append(Q(**{'task': search_form.cleaned_data[each]}))
            elif (each == 'consultant'):
                search_filters.append(Q(**{'consultant': search_form.cleaned_data[each]}))
            elif(each == 'lecture_category'):
                search_filters.append(Q(**{'lecture__lecture_category': search_form.cleaned_data[each]}))
            elif(each == 'feedback_from'):
                search_filters.append(Q(**{'created_at__gte': search_form.cleaned_data[each]}))
            elif (each == 'feedback_to'):
                search_filters.append(Q(**{'created_at__lte': search_form.cleaned_data[each]}))

    if(len(search_filters)>0):
        total_feedback = ConsultantQA.objects.filter(reduce(operator.and_, search_filters)).order_by('-created_at')

    if(request.GET.get('filter')):
        if(request.GET.get('filter') == 'all'):
            total_feedback = ConsultantLecture.objects.filter(reduce(operator.and_, search_filters)).order_by('-created_at')

    context = {
        'form': search_form,
        'total_feedback': total_feedback,
        'consultant_feedback_count': consultant_feedback_count,
    }

    return render(request, 'consultant/consultant_discussion_report.html', context)


def consultant_discussion_feedback_show(request, action, id):
    feedback = ConsultantQA.objects.get(id=id)
    form = ConsultantQAForm()
    comment_list = Comment.objects.filter(consultant_qa=feedback).order_by('-created_date')
    context = {
        'form': form,
        'feedback': feedback,
        'comment_list' : comment_list,
    }

    return render(request, 'consultant/consultant_discussion_report_show.html', context)


def task_distribution_report(request):

    if (request.method == 'POST'):
        form = DivisionSelectionForm(request.POST)
        if (form.is_valid()):
            division = form.cleaned_data['division']
            print(division)
            if(division != None):
                executor_list = User.objects.filter(profile__is_executor=True, profile__division__division_name=division)
                supervisor_list = User.objects.filter(profile__is_supervisor=True, profile__division__division_name=division)
            else:
                executor_list = User.objects.filter(profile__is_executor=True)
                supervisor_list = User.objects.filter(profile__is_supervisor=True)

    else:
        executor_list = User.objects.filter(profile__is_executor=True)
        supervisor_list = User.objects.filter(profile__is_supervisor=True)

    form = DivisionSelectionForm()

    details = {}
    exec_tasks = Task.objects.filter(task_executor__in=executor_list,percent_completed__lt=100).values_list(
        'task_executor__id','task_executor__username','task_executor__profile__division__division_name').annotate(task_count=Count('task_id')).order_by('task_executor__profile__division','-task_count')

    for each in exec_tasks:
        details.update({
            each[0] : [each[1],each[2],each[3]]
        })


    sup_tasks = Task.objects.filter(supervisor__in=supervisor_list,percent_completed__lt=100).values_list(
        'supervisor__id','supervisor__username','supervisor__profile__division__division_name').annotate(task_count=Count('task_id')).order_by('-task_count')

    for each in sup_tasks:
        if(details.get(each[0])):
            details[each[0]].append(each[3])
        else:
            details.update({
                each[0]:[each[1],each[2],0,each[3]]
            })

    # task__percent_completed__lt = 100
    ex_fb_list = ExecutorFeedBack.objects.filter(executor__in=executor_list).values_list(
        'executor_id','executor__username').distinct().annotate(fb_count=Count('id')).order_by('-fb_count')


    for each in ex_fb_list:
        if(details.get(each[0])):
            if(len(details[each[0]]) == 4):
                details[each[0]].append(each[2])
            if(len(details[each[0]]) == 3):
                details[each[0]].append(0)
                details[each[0]].append(each[2])
    context = {
        'task_details':details,
        'form': form,
    }

    return render(request, 'task_management/task_distribution_report.html', context)