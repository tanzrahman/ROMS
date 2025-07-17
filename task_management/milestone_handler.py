import csv
import threading
import datetime
from io import StringIO

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from task_management.models import *
from task_management.notify_users import send_notification
from task_management.system_list import systems as system_list
from task_management.forms import *
from django.db.models import Q
from functools import reduce
import operator

def milestone_list(request):

    page_no = 1
    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = MilestoneSearchForm()
    filters = []
    if(request.GET):
        search_form = MilestoneSearchForm(request.GET)
        if(search_form.is_valid()):
            for each in search_form.changed_data:
                if('date' in each):
                    if('date_from' in each):
                        field_name = each.rsplit('_',1)[0]
                        date_filter = field_name+"__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if('date_to' in each):
                        field_name = each.rsplit('_',1)[0]
                        date_filter = field_name+"__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                if('milestone_id' in each):
                    filters.append(Q(**{'milestone_id__icontains':search_form.cleaned_data[each].upper()}))
                    continue
                if ('title' in each):
                    filters.append(Q(**{'title__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue

                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))


    total = Milestone.objects.all().count()
    milestone_list = Milestone.objects.filter(status='NotStarted').order_by('start_date')
    
    not_started = milestone_list.count()

    if (len(filters) > 0):
        milestone_list = Milestone.objects.filter(reduce(operator.and_, filters))

        src_not_started_milestone = 0
        src_performed_milestone = 0
        src_completed_milestone = 0

        src_assigned = 0

        for milestone in milestone_list:
            if(milestone.status == "NotStarted"):
                src_not_started_milestone += 1
            elif (milestone.status == "Performed"):
                src_performed_milestone += 1
            else:
                src_completed_milestone += 1

            if(milestone.is_assigned==True):
                src_assigned += 1


        src_milestone = milestone_list.count()

        src_unAssigned = src_milestone - src_assigned


    paginator = Paginator(milestone_list, no_of_items)

    try:
        milestone_list = paginator.page(page_no)

    except PageNotAnInteger:
        milestone_list = paginator.page(page_no)

    except EmptyPage:
        milestone_list = paginator.page(paginator.num_pages)



    today = datetime.date.today()
    completed = Milestone.objects.filter(status='Completed').count()
    assigned = Milestone.objects.filter(is_assigned=True).count()
    unassigned = Milestone.objects.filter(is_assigned=False).count()
    this_month = Milestone.objects.filter(is_assigned=False,
                                          status='NotStarted',
                                          start_date__month=today.month,
                                          start_date__year=today.year).count()

    summary = {'not_started':not_started, 'completed':completed, 'assigned':assigned,
               'unassigned':unassigned, 'this_month':this_month, 'total':total}
    context = {'milestone_list': milestone_list, 'summary': summary}

    if (len(filters) > 0):
        context.update({
            'src_milestone':src_milestone,
            'src_completed_milestone':src_completed_milestone,
            'src_unAssigned': src_unAssigned,
            'src_assigned':src_assigned,
        })
    context.update({
        'form':search_form
    })
    return render(request,'task_management/milestone_list.html',context=context)



def verify_milestones(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")

        count = 0
        new_email = {}
        curr_date = datetime.datetime.today()
        print(curr_date)
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:

                milestone_id = row[1].strip()

                if(Task.objects.filter(milestone_id=milestone_id).count()>0):
                    task = Task.objects.filter(milestone_id=milestone_id)
                    for each in task:
                        msg = milestone_id+","+"already assigned by "+each.division.division_name+"\n"
                        failed.write(msg)
                if(Milestone.objects.filter(milestone_id=milestone_id).count()<0):
                    msg = milestone_id + "," + "doesnt exists\n"
                    failed.write(msg)
            except Exception as e:
                msg = "Failed, {}, {}".format(milestone_id, e.__str__())
        failed.close()

        return HttpResponse("Task Assignment Done")