# task list for Russian personnel
import operator
from functools import reduce
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import render
from task_management.forms import AllTaskSearchForm
from task_management.models import *

def ru_task_list(request):
    print("Task_list_ru")
    page_no = 1
    task_list = []
    search_summary = None

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = AllTaskSearchForm(initial={'user':request.user})
    total_tasks = Task.objects.all().count()
    total_monthly_tasks = Task.objects.filter(planned_start_date__month=datetime.datetime.today().month).count()

    filters = []

    if (request.GET):
        search_form = AllTaskSearchForm(request.GET,initial={'user':request.user})
        if (search_form.is_valid()):

            for each in search_form.changed_data:
                if ('date' in each):
                    if ('start_date_from' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('start_date_to' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('end_date_from' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('end_date_to' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                if ('task_id' in each):
                    filters.append(Q(**{'task_id__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('title' in each):
                    filters.append(Q(**{'title__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('supervisor' in each or 'task_executor' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if('task_category' in each):
                    if(search_form.cleaned_data['task_category'][0]!=""):
                        filters.append(Q(**{each+'__in': search_form.cleaned_data[each]}))
                        continue
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    if (len(filters) > 0):
        task_list = Task.objects.filter(reduce(operator.and_, filters))
        search_summary= {
            'total_tasks':task_list.count(),
            'monthly_tasks':task_list.filter(planned_start_date__month=datetime.datetime.today().month).count()
        }
    else:
        task_list = Task.objects.all()

    #get feedback report
    total_feedback = TaskFeedBack.objects.filter(task__in=task_list)
    executor_feedback = ExecutorFeedBack.objects.filter(task__in=task_list)
    supervisor_feedback = SupervisorFeedBack.objects.filter(task__in=task_list)

    day_limit= datetime.datetime.today()-datetime.timedelta(days=3)
    older_than_3_tasks = task_list.filter(updated_date__lt=day_limit,taskfeedback__isnull=True)

    feedback_summary = {'total_feedback': total_feedback, 'executor_feedback': executor_feedback,
                        'supervisor_feedback': supervisor_feedback, 'no_feedback': older_than_3_tasks}


    no_of_items = 100
    paginator = Paginator(task_list, no_of_items)

    try:
        task_list = paginator.page(page_no)

    except PageNotAnInteger:
        task_list = paginator.page(page_no)

    except EmptyPage:
        task_list = paginator.page(paginator.num_pages)

    context = {'task_list': task_list,'total_tasks': total_tasks, 'monthly_tasks': total_monthly_tasks}

    if(search_summary):
        context.update({
            'search_summary':search_summary
        })

    context.update({
        'form':search_form
    })

    context.update({
        'feedback_summary': feedback_summary
    })
    if(request.user.profile.access_level<=4):
        context.update({'user_can_reassign_task':True})
    return render(request, 'russian/ru_task_list.html', context)


def ru_discussion(request):
    lect_list = Lecture.objects.all().order_by('schedule').distinct()

    lect_lead_p = Lecture.objects.filter(lead_presenter=request.user).distinct()
    lect_p = Lecture.objects.filter(other_presenter=request.user).distinct()
    lect_list = lect_list | lect_p | lect_lead_p


    return render(request, 'russian/ru_discussion.html', {'lectures': lect_list})

def ru_open_discussion(request, id):

    lecture = Lecture.objects.get(id=id)
    sv_participants = User.objects.none()
    exec_participants = User.objects.none()
    for each in lecture.tasks.all():
        sv_participants |= each.supervisor.all()
        exec_participants |= each.task_executor.all()

    sv_participants = sv_participants.distinct()
    exec_participants = exec_participants.distinct()

    context = {'lecture': lecture,'sv_participants':sv_participants,'exec_participants':exec_participants}
    return render(request, 'russian/ru_open_discussion.html', context )
