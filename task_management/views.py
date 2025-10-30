import threading
import datetime
import json
from django.core import paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.models import *
from system_log.models import *
from task_management.notify_users import send_notification, send_notification_non_departmental
from task_management.system_list import systems as system_list
from task_management.forms import *
from task_management.milestone_handler import milestone_list
from task_management.milestone_handler import verify_milestones
import csv
from io import StringIO
from task_management.notify_users import send_task_list_notification,task_comment_notification
from task_management.qa_handler import add_question_answer
from task_management.manage_tasks import *
from task_management.qa_handler import add_question_answer,edit_answer,executor_feedback,supervisor_feedback, ongoing_executor_feedback
from task_management.manage_tasks import add_task_consultant, consultant_task_feedback_add_comment, request_consultancy
from time import sleep
from django.db.models import Count

# Create your views here.
def homepage(request):

    if(request.user.is_anonymous):
        return redirect('/login')
    if(request.user.profile.grade>100):
        return redirect('/task_list_ru')
    if(request.user.profile.grade>50 and request.user.profile.grade<100):
        return redirect('/consultant')

    total_documents = Task.objects.filter(created_date__gt='2025-07-31', task_category='DocumentReview').count()

    op_doc = len(OperationalDocumentReview.objects.filter(task__created_date__gt='2025-07-31'))
    regulation_doc = len(RegulationDocumentReview.objects.filter(task__created_date__gt='2025-07-31'))
    fire_doc = len(FireAndEmergencyDocumentReview.objects.filter(task__created_date__gt='2025-07-31'))
    other_doc = len(OthersDocumentReview.objects.filter(task__created_date__gt='2025-07-31'))

    total_1st_tier_review_count = op_doc + regulation_doc + fire_doc + other_doc

    divisions = Division.objects.all()
    total_doc_review = {}
    first_tier_doc_review = {}
    second_tier_doc_review = {}

    for division in divisions:
        total_doc_review.update({str(division): Task.objects.filter(created_date__gt='2025-07-31', division=division, task_category='DocumentReview').count()})

        first_tier_doc_review_count = len(OperationalDocumentReview.objects.filter(task__created_date__gt='2025-07-31', task__division=division)) + len(RegulationDocumentReview.objects.filter(task__created_date__gt='2025-07-31', task__division=division)) \
                              + len(FireAndEmergencyDocumentReview.objects.filter(task__created_date__gt='2025-07-31', task__division=division)) + len(OthersDocumentReview.objects.filter(task__created_date__gt='2025-07-31', task__division=division))

        first_tier_doc_review.update({str(division): first_tier_doc_review_count})

        second_tier_doc_review_count = len(SecondTierDocumentReview.objects.filter(task__created_date__gt='2025-07-31', task__division=division).annotate(count=Count('committee_approval')).order_by('-count'))
        second_tier_doc_review.update({str(division): second_tier_doc_review_count})

    total_2nd_tier_review_count = len(SecondTierDocumentReview.objects.filter(task__created_date__gt='2025-07-31').annotate(count=Count('committee_approval')).order_by('-count'))

    categories = [str(key) for key in first_tier_doc_review.keys()]  # both dicts have same keys in same order

    # Extract values based on the same key order
    total_doc = [total_doc_review[each] for each in categories]
    first_tier_doc = [first_tier_doc_review[each] for each in categories]
    second_tier_doc = [second_tier_doc_review[each] for each in categories]

    series = [
        {'name': 'Total documents', 'data': total_doc},
        {'name': '1st tier review', 'data': first_tier_doc},
        {'name': '2nd tier review', 'data': second_tier_doc},
    ]

    context = {
                'total_1st_tier_review_count': total_1st_tier_review_count,
                'total_2nd_tier_review_count': total_2nd_tier_review_count,
                'total_documents': total_documents,
                'show_notification': True,
                'categories': categories,
                'series': series,
                }

    return render(request, 'task_management/task_management_base.html', context)


def task_request_handler(request,action="",id=""):
    if(request.user.is_anonymous):
        return redirect('/')

    if (request.user.profile.grade > 75):
        return redirect('/ru')
    if(request.user.profile.grade > 25):
        return redirect('/consultant')
    if(action == 'consultancy_requests'):
        return consultancy_request(request)
    if(action == 'consultancy_request_approval'):
        return consultancy_request_approval(request, id)
    if(action == 'milestone_list'):
        return milestone_list(request)
    if(action=='task_list'):
        return task_list(request)
    if(action=='started_task_list'):
        return started_task_list(request)
    if(action == 'my_task'):
        return my_task_list(request)
    if (action == 'assigned_task'):
        return assigned_task(request)
    if(action == 'add_task'):
        return add_task(request)
    if(action == 'me_upload_task'):
        return me_upload_task(request)
    if(action == 'dp_upload_task'):
        return upload_duplicate_task(request)
    if (action == 'nm_upload_task'):
        return upload_non_milestone_task(request)
    if(action == 'open_task'):
        return open_task(request,id)
    if(action == 'edit_task'):
        return edit_task(request,id)
    if(action == 'upload_task'):
        return upload_task(request)
    if(action == 'reassign_task'):
        return task_reassignment(request)
    if (action == 'upload_milestone'):
        return upload_milestone(request)
    if (action == 'facility_parse'):
        return facility_parser(request)
    if (action == 'add_person'):
        return add_person(request,id)
    if (action == 'add_comment'):
        return add_comment(request, id)
    if (action == 'add_answer'):
        return add_question_answer(request, id)
    if(action == 'edit_answer'):
        return edit_answer(request,id)
    if(action == 'user_task_list'):
        return user_task_list(request,id)
    if(action == 'verify'):
        return verify_milestones(request)
    if(action == 'executor_feedback'):
        return executor_feedback(request, id)
    if (action == 'supervisor_feedback'):
        return supervisor_feedback(request, id)
    if(action == 'suggest_task'):
        return task_suggestion(request, id)
    if(action == 'add_actual_start_date'):
        return add_actual_start_date(request, id)
    if(action == 'add_actual_end_date'):
        return add_actual_end_date(request, id)
    if(action == 'lead_exec'):
        return add_lead_executor(request,id)
    if(action == 'task_details'):
        return task_details(request,id)
    if(action == 'ongoing_executor_feedback'):
        return ongoing_executor_feedback(request,id)
    if(action == 'add_task_consultant'):
        return add_task_consultant(request,id)
    if(action == 'consultant_task_feedback_add_comment'):
        return consultant_task_feedback_add_comment(request,id)
    if(action == 'request_consultancy'):
        return request_consultancy(request,id)
    if(action == 'task_comment'):
        return task_comment(request, id)
    if(action == 'add_task_percentage'):
        return add_task_percentage(request, id)
    if(action == 'update_saw_schedule'):
        return update_saw_level2_schedule(request)
    if(action == 'op_doc_upload'):
        return upload_operational_document(request)
    else:
        return HttpResponse("Invalid Access")


def user_task_list(request,user_id):
    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')
    user = User.objects.get(id=user_id)
    today = datetime.date.today()
    one_month = datetime.date.today() + datetime.timedelta(days=30)
    task_list = Task.objects.filter(task_executor=user,planned_start_date__gt=today,
                                    planned_start_date__lt=one_month
                                    ).values('task_id','planned_start_date').order_by('planned_start_date')
    total_tasks = len(task_list)
    tasks = []
    tasks.append({"total_tasks": total_tasks, "user":user.first_name+" "+user.last_name})
    if(total_tasks > 0):
        for each in task_list:
            tasks.append(each)
    return JsonResponse(tasks, safe=False)

def add_person(request,task_id):

    task = Task.objects.get(id=int(task_id))
    form = AddPersonForm(initial={'user':request.user})

    if(request.method == 'GET'):
        return render(request,'task_management/add_persion.html',{'form':form,'task':task})

    if(request.method == 'POST'):
        form = AddPersonForm(request.POST,initial={'user': request.user})
        if(form.is_valid()):
            supervisors = form.cleaned_data['supervisor']
            executors = form.cleaned_data['executor']

            for supervisor in supervisors:
                task.supervisor.add(supervisor)
            for executor in executors:
                task.task_executor.add(executor)
            task.save()

            notifiyer = threading.Thread(target=send_notification_non_departmental, args=(task_id,))
            notifiyer.start()

            return render(request, 'task_management/add_persion.html', {'success':'success', 'task': task})

        return render(request,'task_management/add_persion.html',{'form':form,'task':task})


def add_comment(request, task_id):

    task = Task.objects.get(id=int(task_id))
    form = CommentForm(initial={'user': request.user, 'task_id': task_id})

    if(request.method == 'GET'):
        return render(request,'task_management/add_comment.html', {'form': form, 'task': task})

    if(request.method == 'POST'):
        form = CommentForm(request.POST, initial={'user': request.user, 'task_id': task_id})
        if(form.is_valid()):
            add_comment = form.save(commit=False)
            add_comment.user = request.user
            add_comment.created_date = datetime.datetime.now()
            add_comment.save()

            th = threading.Thread(target=task_comment_notification,args =(task,request.user))
            th.start()
            message = "Comment has been added successfully"

        return render(request,'task_management/add_comment.html', {'form': form, 'task': task, 'message': message})






def my_task_list(request):

    page_no = 1
    no_of_items = 100

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    search_form = TaskSearchForm(initial={'user': request.user})
    filters = []
    if (request.GET):
        search_form = TaskSearchForm(request.GET, initial={'user': request.user})
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
                if ('milestone_id' in each):
                    filters.append(Q(**{'milestone_id__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('supervisor' in each or 'task_executor' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))

                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    assigned_task = Task.objects.filter(created_date__gt='2025-07-31').filter(task_executor=request.user).order_by('planned_start_date')
    total_assigned_task = assigned_task.count()

    monthly_assigned = Task.objects.filter(task_executor=request.user).filter(created_date__gt='2025-07-31').filter(planned_start_date__year=datetime.datetime.today().year, planned_start_date__month=datetime.datetime.today().month).count()

    src_total_assigned_task = 0
    if (len(filters) > 0):
        assigned_task = Task.objects.filter(created_date__gt='2025-07-31').filter(task_executor=request.user).filter(reduce(operator.and_, filters))
        src_total_assigned_task = assigned_task.count()

    assigned_task = assigned_task.exclude(task_category='DocumentReview')
    paginator = Paginator(assigned_task, no_of_items)

    try:
        assigned_task = paginator.page(page_no)

    except PageNotAnInteger:
        assigned_task = paginator.page(page_no)

    except EmptyPage:
        assigned_task = paginator.page(paginator.num_pages)

    context = {'assigned_task': assigned_task, 'total_assigned_task': total_assigned_task, 'monthly_assigned': monthly_assigned,}

    if (len(filters) > 0):
        context.update({
            'src_total_assigned_task': src_total_assigned_task,
        })
    context.update({
        'form': search_form
    })

    return render(request,'task_management/task_list.html', context)


def assigned_task(request):

    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = TaskSearchForm(initial={'user':request.user})
    filters = []
    if (request.GET):
        search_form = TaskSearchForm(request.GET,initial={'user':request.user})
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
                if ('milestone_id' in each):
                    filters.append(Q(**{'milestone_id__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('title' in each):
                    filters.append(Q(**{'title__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('supervisor' in each or 'task_executor' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))

                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    assigned_task = Task.objects.filter(created_date__gt='2025-07-31').filter(supervisor=request.user).order_by('planned_start_date')
    total_assigned_task = assigned_task.count()

    monthly_assigned = Task.objects.filter(supervisor=request.user).filter(created_date__gt='2025-07-31').filter(
         planned_start_date__year=datetime.datetime.today().year, planned_start_date__month=datetime.datetime.today().month).count()

    src_total_assigned_task = 0
    if (len(filters) > 0):
        assigned_task = Task.objects.filter(created_date__gt='2025-07-31').filter(supervisor=request.user).filter(reduce(operator.and_, filters))
        src_total_assigned_task = assigned_task.count()

    paginator = Paginator(assigned_task, no_of_items)

    try:
        assigned_task = paginator.page(page_no)

    except PageNotAnInteger:
        assigned_task = paginator.page(page_no)

    except EmptyPage:
        assigned_task = paginator.page(paginator.num_pages)

    context = {'assigned_task': assigned_task, 'total_assigned_task': total_assigned_task, 'monthly_assigned': monthly_assigned,}

    if (len(filters) > 0):
        context.update({
            'src_total_assigned_task': src_total_assigned_task,
        })
    context.update({
        'form': search_form
    })
    return render(request, 'task_management/assigned_task.html', context=context)


def add_task(request):
    if (request.user.profile.access_level > 6):
        if(not request.user.profile.is_supervisor):
            return HttpResponse("You Dont Have The Permission to Assign a new Task")
    initial = {}

    milestone_id = -1
    if(request.GET.get('milestone_id')):
        milestone_id = int(request.GET.get('milestone_id'))

    initial.update({
        'division': request.user.profile.division
    })

    # initial.update({
    #     'department': request.user.profile.department
    # })
    #
    #
    # initial.update({
    #     'subdepartment': request.user.profile.subdepartment
    # })
    #
    # initial.update({
    #     'section': request.user.profile.section
    # })
    initial.update({
        'creating_user': request.user
    })

    if(milestone_id>0):
        milestone = Milestone.objects.get(id=milestone_id)
        initial.update({
            'milestone_id': milestone.milestone_id
        })
        if (milestone.facility != ""):
            facility = Facility.objects.get(kks_code=milestone.facility)
            initial.update({
                'facility':facility,
                'relevant_kks_codes':facility
            })
            initial.update({
                'title': milestone.title
            })
            initial.update({
                'planned_start_date':milestone.start_date,
                'planned_end_date':milestone.end_date
            })
            if(milestone.start_date <= datetime.date.today()):
                initial.update({
                    'actual_start_date':milestone.start_date
                })
            if (milestone.end_date <= datetime.date.today()):
                initial.update({
                    'actual_end_date': milestone.end_date
                })
            if(milestone.system):
                initial.update({
                    'system':milestone.system
                })
            if(milestone.task_id):
                initial.update({
                    'task_id':milestone.task_id
                })



    if request.method == 'POST':
        form = TaskForm(request.POST,initial=initial)

        context = {}

        if form.is_valid():
            f_task = form.save(commit=False)
            f_task.created_date = datetime.date.today()
            f_task.task_created_by = request.user
            f_task.status = '1'
            f_task.is_active = True
            f_task.save()
            if(not f_task.percent_completed):
                f_task.percent_completed = 0
            task_id = f_task.id
            for each in form.cleaned_data['supervisor']:
                f_task.supervisor.add(each)
            for each in form.cleaned_data['task_executor']:
                f_task.task_executor.add(each)
            f_task.save()


            notifiyer = threading.Thread(target=send_notification, args=(task_id,))
            notifiyer.start()


            add_task_form = TaskForm()
            context = {'form': add_task_form, 'success':'True'}
        else:
            context = {'form': form}
        return render(request, 'task_management/add_task.html', context)

    else:
        add_task_form = TaskForm(initial=initial)

        context = {'form': add_task_form}

        return render(request, 'task_management/add_task.html', context)


def open_task(request, task_id):

    task = Task.objects.get(id=task_id)
    supervisor_list = TaskSupervisorLink.objects.filter(task_id=task)
    executor_list = TaskExecutorLink.objects.filter(task_id=task)
    comment_list = Comment.objects.filter(task_id=task).order_by('-created_date')
    question_answer_list = QuestionsAnswers.objects.filter(task_id=task,answered_by=request.user)

    ts_link = None
    te_link = None
    hide_read_confirm = True
    if request.user in task.supervisor.all():
        if(TaskSupervisorLink.objects.filter(task_id=task,supervisor=request.user).count()==0):
            ts_link = TaskSupervisorLink.objects.create(task_id=task, task_acknowledged=1,
                                                task_opened_time=datetime.datetime.now(),supervisor=request.user)
        else:
            ts_link = TaskSupervisorLink.objects.get(task_id=task, supervisor=request.user)

    if(request.user in task.task_executor.all()):
        if (TaskExecutorLink.objects.filter(task_id=task, executor=request.user).count() == 0):
            te_link = TaskExecutorLink.objects.create(task_id=task, task_acknowledged=1,
                                                task_opened_time=datetime.datetime.now(),executor=request.user)
        else:
            te_link = TaskExecutorLink.objects.get(task_id=task, executor=request.user)

    if (request.GET.get('document_read')):
        if (request.GET.get('document_read')[0]=='1'):
            if(te_link):
                te_link.document_read = 1
                te_link.save()
                hide_read_confirm = True
            if(ts_link):
                ts_link.document_read = 1
                ts_link.save()
                hide_read_confirm = True

    task_feedback = None
    if(TaskFeedBack.objects.filter(task=task).count()>0):
        task_feedback = TaskFeedBack.objects.get(task=task)

    user_type = ""
    if(request.user in task.supervisor.all()):
        user_type = 'supervisor'
    elif(request.user in task.task_executor.all()):
        user_type = 'executor'
    elif(request.user.profile.access_level==4):
        user_type = 'distributor'
    elif(request.user.profile.access_level==3):
        user_type = 'division_head'
    elif (request.user.profile.access_level <3):
        user_type = 'management'

    context = {
                'task': task,
                'comment_list': comment_list,
                'question_answer_list': question_answer_list,
                'task_feed_back':task_feedback,
                'supervisors': supervisor_list,
                'executors': executor_list,
                'user_type': user_type
            }
    if(hide_read_confirm):
        context.update({
            'hide_confirm':True
        })

    return render(request, 'task_management/open_task.html', context)


def upload_task(request):
    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        password = 'vver1200@RNPP'
        count = 0
        new_email = {}
        curr_date = datetime.date.today()
        print(curr_date)
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:
                facility_kks = row[0].strip()
                milestone_id = row[1].strip()
                job_id = row[2].strip()
                title = row[3].strip()
                stage = row[4].strip().upper()
                system = row[5].strip().upper()
                sub_sys = row[6].strip().upper()

                supervisor_1_phone = row[7].strip()
                supervisor_1_email = row[8].strip().replace(' ','').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ','').lower()


                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ','').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ','').lower()

                division = row[15].strip()
                division_obj = None

                if(Division.objects.filter(division_name=division).count()<1):
                    division_obj = Division.objects.create(division_name=division)
                else:
                    division_obj = Division.objects.filter(division_name=division).first()


                facilty_obj = None
                milestone_obj = None
                system_obj = None
                sub_system_obj = None
                supervisor_2 = None
                executor_2 = None

                if(system!=""):
                    if(System.objects.filter(name=system).count()<1):
                        system_obj = System.objects.create(name=system)
                if(sub_sys!=""):
                    if(SubSystem.objects.filter(name=sub_sys).count()<1):
                        sub_system_obj = SubSystem.objects.create(name=sub_sys)
                        if (system_obj):
                            sub_system_obj.system=system_obj
                            sub_system_obj.save()


                #if task with this milestone already created, ignore it
                if(Task.objects.filter(milestone_id=milestone_id).count()>0):
                    print("Mileston ID Task Already Created")
                    task = Task.objects.filter(milestone_id=milestone_id).first()
                    msg = "Task already created with milestone id, {},by {}\n".format(milestone_id,task.division)
                    failed.write(msg)
                    continue
                if(executor_1_email == "" and executor_2_email==""):
                    msg = "NO Executor in milestone,{}\n".format(milestone_id)
                    failed.write(msg)
                    continue


                #if facility doesn't exists, create facility
                facility_filter = Facility.objects.filter(kks_code=facility_kks)
                if(facility_filter.count()<1):
                    facilty_obj= Facility.objects.create(kks_code=facility_kks, name=facility_kks)
                else:
                    facilty_obj = facility_filter.first()

                #get the Milestone from existing milestone table
                milestone_filter = Milestone.objects.filter(milestone_id=milestone_id)

                if(milestone_filter.count()<1):
                    failed.write(str(milestone_id) + "NOT FOUND IN EXISTING DATABASE")
                else:
                    milestone_obj = milestone_filter.first()
                    milestone_obj.facility = facilty_obj.kks_code
                    milestone_obj.is_assigned = True
                    milestone_obj.division=division_obj

                    supervisor_1 = get_user(supervisor_1_email, supervisor_1_phone,division_obj,new_user,is_supervisor=True)

                    supervisor_2 = get_user(supervisor_2_email, supervisor_2_phone,division_obj,new_user,is_supervisor=True)

                    executor_1 = get_user(executor_1_email,executor_1_phone,division_obj,new_user,is_supervisor=False)
                    executor_2 = get_user(executor_2_email, executor_2_phone, division_obj, new_user,is_supervisor=False)

                    new_task = Task(task_id=milestone_obj.task_id, milestone_id=milestone_obj.milestone_id,
                                    relevant_kks_codes=facilty_obj.kks_code, title=milestone_obj.title,
                                    description=milestone_obj.title,planned_start_date=milestone_obj.start_date,
                                    planned_end_date=milestone_obj.end_date,created_date=curr_date,task_created_by=supervisor_1,
                                    facility=facilty_obj, stage=stage,division=division_obj,
                                    is_active=True,status='N',system=system_obj,subsystem=sub_system_obj
                                    )
                    new_task.save()

                    new_task.supervisor.add(supervisor_1)
                    if(supervisor_2):
                        new_task.supervisor.add(supervisor_2)

                    new_task.task_executor.add(executor_1)
                    if(executor_2):
                        new_task.task_executor.add(executor_2)

                    new_task.save()
                    milestone_obj.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id,e.__str__())
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")


def upload_milestone(request):
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')
    if(request.method == 'POST'):
        if (request.method == 'POST'):
            file = request.FILES['user_csv'].file.read()
            reader = csv.reader(StringIO(file.decode('utf-8')))
            output = open("failed.txt", "w")
            un_identified = open("unidentified.txt", "w")
            facilities = list(Facility.objects.all().values_list('kks_code',flat=True))
            #print(facilities)
            bulk_items = []
            for row in reader:
                try:
                    job_id = row[0].strip()
                    status = row[1]
                    milestone_id = row[2].strip()
                    name = row[3]
                    task_id = row[4].strip()
                    length = row[5]
                    start_date = row[6].strip()
                    end_date = row[7].strip()
                    start_date = datetime.datetime.strptime(start_date,'%m/%d/%Y')
                    end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
                    completed = False
                    active = True
                    facility = ""
                    if(Milestone.objects.filter(milestone_id=milestone_id,).count()>0):
                        continue

                    if(status == 'Completed'):
                        completed = True
                    system = None
                    for each in system_list:
                        if(each in name):
                            system = System.objects.get(name=each)
                            print(milestone_id," ,",each)
                            break
                    for each in facilities:
                        if (each in job_id):
                            facility = each
                            break
                    if(facility==""):
                        for each in facilities:
                            if (each in milestone_id):
                                facility = each
                                break
                    if(not system):
                        msg = "Failed identify system, {}\n".format(milestone_id)
                        un_identified.write(msg)

                    if(system):
                        new_milestone = Milestone(milestone_id=milestone_id,job_id=job_id,task_id=task_id,title=name
                                                  ,status=status,is_active=active,is_completed=completed
                                                  ,facility=facility, start_date=start_date,end_date=end_date
                                                  ,system=system)
                        bulk_items.append(new_milestone)
                    else:
                        new_milestone = Milestone(milestone_id=milestone_id, job_id=job_id, task_id=task_id,title=name
                                                  , status=status, is_active=active, is_completed=completed,
                                                  facility=facility, start_date=start_date, end_date=end_date)
                        bulk_items.append(new_milestone)

                    if(len(bulk_items)==500):
                        Milestone.objects.bulk_create(bulk_items,ignore_conflicts=True,batch_size=500)
                        bulk_items = []

                except Exception as e:
                    msg = "Failed to insert: {},\t{}\n".format(milestone_id,e.__str__())
                    output.write(msg)
            if(len(bulk_items)>0):
                print("Inserting remaining items: ",len(bulk_items))
                Milestone.objects.bulk_create(bulk_items, ignore_conflicts=True)

            output.close()
            un_identified.close()




        return HttpResponse("Task Updated")

def facility_parser(request):
    m_list = Milestone.objects.all()
    for each in m_list:
        if(not each.facility):
            segmented_data = each.milestone_id.split('.')
            if (len(segmented_data) > 6):
                facility_kks = segmented_data[4]
                if (len(facility_kks) > 2):
                    print("Facility:", facility_kks)
                    each.facility = facility_kks
                    if(Facility.objects.filter(kks_code=facility_kks).count() == 0):
                        new_fac = Facility.objects.create(kks_code=facility_kks)

                    each.save()
                else:
                    print("Non Facility: ", facility_kks)
    return HttpResponse("Facility Parsing Done")


def me_upload_task(request):
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        task_category = None
        new_task = None
        if(request.GET.get('task_category')):
            task_category = request.GET.get('task_category')
        if(request.GET.get('new_task')):
            new_task = True

        count = 0
        new_email = {}
        curr_date = datetime.date.today()
        start_date = None
        end_date = None
        actual_start = None

        print(curr_date)
        password = "vver1200@RNPP"
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:
                facility_kks = row[0].strip()
                milestone_id = row[1].strip()
                job_id = row[2].strip()
                title = row[3].strip()
                stage = row[4].strip().upper()
                system = row[5].strip().upper()
                sub_sys = row[6].strip().upper()

                supervisor_1_phone = row[7].strip()
                supervisor_1_email = row[8].strip().replace(' ','').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ','')


                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ','').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ','').lower()

                division = row[15].strip()
                division_obj = None

                if (new_task == None):
                    if(len(row)>16):
                        executor_3_phone = row[16].strip()
                        executor_3_email = row[17].strip().replace(' ', '').lower()
                    if(len(row)>18):
                        executor_4_phone = row[18].strip()
                        executor_4_email = row[19].strip().replace(' ', '').lower()
                else:
                    start_date = row[16].strip()
                    end_date = row[17].strip()
                    actual_start = row[18].strip()

                if(Division.objects.filter(division_name=division).count()<1):
                    division_obj = Division.objects.create(division_name=division)
                else:
                    division_obj = Division.objects.filter(division_name=division).first()


                facilty_obj = None
                milestone_obj = None
                system_obj = None
                sub_system_obj = None
                supervisor_2 = None
                executor_2 = None
                executor_3 = None
                executor_4 = None

                if(system!=""):
                    if(System.objects.filter(name=system).count()<1):
                        system_obj = System.objects.create(name=system)
                if(sub_sys!=""):
                    if(SubSystem.objects.filter(name=sub_sys).count()<1):
                        sub_system_obj = SubSystem.objects.create(name=sub_sys)
                        if (system_obj):
                            sub_system_obj.system=system_obj
                            sub_system_obj.save()


                #if task with this milestone already created, ignore it
                if(Task.objects.filter(milestone_id=milestone_id).count()>0):
                    print("Mileston ID Task Already Created")
                    msg = "Task already created with milestone id, {}\n".format(milestone_id)
                    failed.write(msg)
                    continue


                #if facility doesn't exists, create facility
                facility_filter = Facility.objects.filter(kks_code=facility_kks)
                if(facility_filter.count()<1):
                    facilty_obj= Facility.objects.create(kks_code=facility_kks, name=facility_kks)
                else:
                    facilty_obj = facility_filter.first()

                #get the Milestone from existing milestone table
                milestone_filter = Milestone.objects.filter(milestone_id=milestone_id)

                if(milestone_filter.count()<1 and new_task == None):
                    failed.write(str(milestone_id) + "NOT FOUND IN EXISTING DATABASE")
                else:

                    milestone_obj = None
                    if(milestone_filter.count()>0):
                        milestone_obj = milestone_filter.first()
                        milestone_obj.facility = facilty_obj.kks_code
                        milestone_obj.is_assigned = True
                        milestone_obj.division=division_obj

                    supervisor_1 = get_user(supervisor_1_email, supervisor_1_phone, division_obj, new_user,
                                            is_supervisor=True)

                    supervisor_2 = get_user(supervisor_2_email, supervisor_2_phone, division_obj, new_user,
                                            is_supervisor=True)

                    executor_1 = get_user(executor_1_email, executor_1_phone, division_obj, new_user,
                                          is_supervisor=False)
                    executor_2 = get_user(executor_2_email, executor_2_phone, division_obj, new_user,
                                          is_supervisor=False)

                    if (new_task == None):
                        if (len(row) > 16):
                            executor_3 = get_user(executor_3_email, executor_3_phone, division_obj, new_user,
                                              is_supervisor=False)
                        if (len(row) > 18):
                            executor_4 = get_user(executor_4_email, executor_4_phone, division_obj, new_user,
                                              is_supervisor=False)


                    if(milestone_obj != None):
                        new_task_obj = Task(task_id=milestone_obj.task_id, milestone_id=milestone_obj.milestone_id,
                                        relevant_kks_codes=facilty_obj.kks_code, title=milestone_obj.title,
                                        description=milestone_obj.title,planned_start_date=milestone_obj.start_date,
                                        planned_end_date=milestone_obj.end_date,created_date=curr_date,task_created_by=supervisor_1,
                                        facility=facilty_obj, stage=stage,division=division_obj,
                                        is_active=True,status='N',system=system_obj,subsystem=sub_system_obj
                                        )
                        new_task_obj.save()
                    else:
                        new_task_obj = Task(task_id=job_id, milestone_id=milestone_id,
                                        relevant_kks_codes=facilty_obj.kks_code, title=title,
                                        description=title, planned_start_date=start_date,
                                        planned_end_date=end_date, created_date=curr_date,
                                        task_created_by=supervisor_1,
                                        facility=facilty_obj, stage=stage, division=division_obj,
                                        is_active=True, status='N', system=system_obj, subsystem=sub_system_obj
                                        )
                        new_task_obj.save()

                    new_task_obj.supervisor.add(supervisor_1)
                    if(supervisor_2):
                        new_task_obj.supervisor.add(supervisor_2)

                    new_task_obj.task_executor.add(executor_1)
                    if(executor_2):
                        new_task_obj.task_executor.add(executor_2)

                    if(executor_3):
                        new_task_obj.task_executor.add(executor_3)

                    if(executor_4):
                        new_task_obj.task_executor.add(executor_4)

                    new_task_obj.save()
                    if(new_task is None):
                        milestone_obj.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id,e.__str__())
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")


def upload_duplicate_task(request):
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        password = 'vver1200@RNPP'
        count = 0
        new_email = {}
        curr_date = datetime.date.today()
        print(curr_date)
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:
                facility_kks = row[0].strip()
                milestone_id = row[1].strip()
                job_id = row[2].strip()
                title = row[3].strip()
                stage = row[4].strip().upper()
                system = row[5].strip().upper()
                sub_sys = row[6].strip().upper()

                supervisor_1_phone = row[7].strip()
                supervisor_1_email = row[8].strip().replace(' ','').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ','')


                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ','').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ','').lower()

                division = row[15].strip()
                division_obj = None

                if(Division.objects.filter(division_name=division).count()<1):
                    division_obj = Division.objects.create(division_name=division)
                else:
                    division_obj = Division.objects.filter(division_name=division).first()


                facilty_obj = None
                milestone_obj = None
                system_obj = None
                sub_system_obj = None
                supervisor_2 = None
                executor_2 = None

                if(system!=""):
                    if(System.objects.filter(name=system).count()<1):
                        system_obj = System.objects.create(name=system)
                if(sub_sys!=""):
                    if(SubSystem.objects.filter(name=sub_sys).count()<1):
                        sub_system_obj = SubSystem.objects.create(name=sub_sys)
                        if (system_obj):
                            sub_system_obj.system=system_obj
                            sub_system_obj.save()


                if(executor_1_email == "" and executor_2_email==""):
                    msg = "NO Executor in milestone,{}\n".format(milestone_id)
                    failed.write(msg)
                    continue


                #if facility doesn't exists, create facility
                facility_filter = Facility.objects.filter(kks_code=facility_kks)
                if(facility_filter.count()<1):
                    facilty_obj= Facility.objects.create(kks_code=facility_kks, name=facility_kks)
                else:
                    facilty_obj = facility_filter.first()

                #get the Milestone from existing milestone table
                milestone_filter = Milestone.objects.filter(milestone_id=milestone_id)

                if(milestone_filter.count()<1):
                    failed.write(str(milestone_id) + "NOT FOUND IN EXISTING DATABASE")
                else:
                    milestone_obj = milestone_filter.first()
                    milestone_obj.facility = facilty_obj.kks_code
                    milestone_obj.is_assigned = True
                    milestone_obj.division=division_obj

                    supervisor_1 = get_user(supervisor_1_email, supervisor_1_phone,division_obj,new_user,is_supervisor=True)

                    supervisor_2 = get_user(supervisor_2_email, supervisor_2_phone,division_obj,new_user,is_supervisor=True)

                    executor_1 = get_user(executor_1_email,executor_1_phone,division_obj,new_user,is_supervisor=False)
                    executor_2 = get_user(executor_2_email, executor_2_phone, division_obj, new_user,is_supervisor=False)

                    new_task = Task(task_id=milestone_obj.task_id, milestone_id=milestone_obj.milestone_id,
                                    relevant_kks_codes=facilty_obj.kks_code, title=milestone_obj.title,
                                    description=milestone_obj.title,planned_start_date=milestone_obj.start_date,
                                    planned_end_date=milestone_obj.end_date,created_date=curr_date,task_created_by=supervisor_1,
                                    facility=facilty_obj, stage=stage,division=division_obj,
                                    is_active=True,status='N',system=system_obj,subsystem=sub_system_obj
                                    )
                    new_task.save()

                    new_task.supervisor.add(supervisor_1)
                    if(supervisor_2):
                        new_task.supervisor.add(supervisor_2)

                    new_task.task_executor.add(executor_1)
                    if(executor_2):
                        new_task.task_executor.add(executor_2)

                    new_task.save()
                    milestone_obj.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id,e.__str__())
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")


def upload_non_milestone_task(request):
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        password = 'vver1200@RNPP'
        count = 0
        new_email = {}
        curr_date = datetime.date.today()
        print(curr_date)
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:
                facility_kks = row[0].strip()
                milestone_id = row[1].strip()
                job_id = row[2].strip()
                title = row[3].strip()
                stage = row[4].strip().upper().replace('\n',',')
                system = row[5].strip().upper().replace('.','')
                sub_sys = row[6].strip().upper().replace('.','')

                supervisor_1_phone = row[7].strip()
                supervisor_1_email = row[8].strip().replace(' ','').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ','').lower()


                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ','').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ','').lower()

                planned_start = row[15].strip()
                planned_end = row[16].strip()
                division = row[17].strip()
                task_category = row[18].strip()

                if(len(row)>19):
                    executor_3_phone = row[19].strip()
                    executor_3_email = row[20].strip().replace(' ', '').lower()

                if (len(row) > 21):
                    executor_4_phone = row[21].strip()
                    executor_4_email = row[22].strip().replace(' ', '').lower()

                if (len(row) > 23):
                    executor_5_phone = row[23].strip()
                    executor_5_email = row[24].strip().replace(' ', '').lower()

                if (len(row) > 25):
                    executor_6_phone = row[25].strip()
                    executor_6_email = row[26].strip().replace(' ', '').lower()

                if (len(row) > 27):
                    executor_7_phone = row[27].strip()
                    executor_7_email = row[28].strip().replace(' ', '').lower()

                if(planned_end ==""):
                    planned_end = None

                division_obj = None

                if(Division.objects.filter(division_name=division).count()<1):
                    division_obj = Division.objects.create(division_name=division)
                else:
                    division_obj = Division.objects.filter(division_name=division).first()


                facilty_obj = None
                milestone_obj = None
                system_obj = None
                sub_system_obj = None
                supervisor_2 = None
                executor_2 = None
                executor_3 = None
                executor_4 = None
                executor_5 = None
                executor_6 = None
                executor_7 = None

                if(system!=""):
                    if(System.objects.filter(name=system).count()<1):
                        system_obj = System.objects.create(name=system)
                if(sub_sys!=""):
                    if(SubSystem.objects.filter(name=sub_sys).count()<1):
                        sub_system_obj = SubSystem.objects.create(name=sub_sys)
                        if (system_obj):
                            sub_system_obj.system=system_obj
                            sub_system_obj.save()


                if(executor_1_email == "" and executor_2_email==""):
                    msg = "NO Executor in milestone,{}\n".format(milestone_id)
                    failed.write(msg)
                    continue


                #if facility doesn't exists, create facility
                facility_filter = Facility.objects.filter(kks_code=facility_kks)
                if(facility_filter.count()<1):
                    facilty_obj= Facility.objects.create(kks_code=facility_kks, name=facility_kks)
                else:
                    facilty_obj = facility_filter.first()

            #get the Milestone from existing milestone table


                supervisor_1 = get_user(supervisor_1_email, supervisor_1_phone,division_obj,new_user,is_supervisor=True)

                supervisor_2 = get_user(supervisor_2_email, supervisor_2_phone,division_obj,new_user,is_supervisor=True)

                executor_1 = get_user(executor_1_email,executor_1_phone,division_obj,new_user,is_supervisor=False)
                executor_2 = get_user(executor_2_email, executor_2_phone, division_obj, new_user,is_supervisor=False)

                if (len(row) > 19):
                    if(len(executor_3_email)>12):
                        executor_3 = get_user(executor_3_email, executor_3_phone,division_obj, new_user,is_supervisor=False)

                if (len(row) > 21):
                    if(len(executor_4_email)>12):
                        executor_4 = get_user(executor_4_email, executor_4_phone, division_obj, new_user,is_supervisor=False)

                if (len(row) > 23):
                    if(len(executor_5_email)>12):
                        executor_5 = get_user(executor_5_email, executor_5_phone, division_obj, new_user,is_supervisor=False)

                if (len(row) > 25):
                    if(len(executor_6_email)>12):
                        executor_6 = get_user(executor_6_email, executor_6_phone, division_obj, new_user,is_supervisor=False)

                if (len(row) > 27):
                    if(len(executor_7_email)>12):
                        executor_7 = get_user(executor_7_email,executor_7_phone, division_obj, new_user,is_supervisor=False)

                new_task = Task(task_id=job_id, milestone_id=milestone_id,
                                relevant_kks_codes=facilty_obj.kks_code, title=title,
                                description=title,planned_start_date=planned_start,
                                planned_end_date=planned_end,created_date=curr_date,task_created_by=supervisor_1,
                                facility=facilty_obj, stage=stage,division=division_obj,
                                is_active=True,status='N',system=system_obj,subsystem=sub_system_obj,task_category=task_category
                                )
                new_task.save()

                new_task.supervisor.add(supervisor_1)
                if(supervisor_2):
                    new_task.supervisor.add(supervisor_2)

                new_task.task_executor.add(executor_1)
                if(executor_2):
                    new_task.task_executor.add(executor_2)

                if(executor_3):
                    new_task.task_executor.add(executor_3)

                if(executor_4):
                    new_task.task_executor.add(executor_4)

                if (executor_5):
                    new_task.task_executor.add(executor_5)

                if (executor_6):
                    new_task.task_executor.add(executor_6)

                if (executor_7):
                    new_task.task_executor.add(executor_7)


                new_task.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id,e.__str__())
                print(msg)
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")

def handle_launch(request):

    if(request.user.is_anonymous):
        return redirect('/login')
    context = {'success': True}
    if(request.GET.get('launch')):
        launch = SystemParameter.objects.filter(name='launch').first()
        launch.value = 1
        launch.save()
        today = datetime.date.today()
        seven_days = datetime.date.today() + datetime.timedelta(days=7)
        task_list = Task.objects.filter(status='N',planned_start_date__gt=today,
                                        planned_start_date__lt=seven_days)
        sms_count = 0
        for each in task_list:
            sms_count += each.supervisor.all().count() + each.task_executor.all().count()

        print("total task: {}, sms: {}".format(task_list.count(),sms_count))
        context.update({
            'tasks':task_list.count(),
            'person':sms_count
        })
        task_list = task_list.values_list('id',flat=True)
        thread = threading.Thread(target=send_task_list_notification,args=(task_list,))
        thread.start()
        sleep(2)

        return render(request, 'project_launch.html',context)

    return render(request, 'project_launch.html')

def task_details(request,id):
    print(id)
    task = Task.objects.get(id=id)

    task_details = ("Title: {}, \n"
                    "Supervisors: {}, Executors: {},\n"
                    " Planned Start: {}").format(task.title,task.supervisor.count(),task.task_executor.count(),task.planned_start_date)

    print(task_details)

    return JsonResponse(task_details,safe=False)


def consultancy_request(request):

    search_form = ConsultancyRequestSearchForm()

    filters = []

    if (request.GET):
        search_form = ConsultancyRequestSearchForm(request.GET)
        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('date' in each):
                    if ('request_date_from' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('request_date_to' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                if ('task_id' in each):
                    filters.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if (each=='consultant'):
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))
                    continue
                if (each=='division'):
                    filters.append(Q(**{'task__'+ each: search_form.cleaned_data[each]}))
                    continue
                if (each=='task_category'):
                    filters.append(Q(**{'task__'+ each: search_form.cleaned_data[each]}))
                    continue
                if(each == 'status'):
                    if(search_form.cleaned_data[each]=='all'):
                        continue
                    if(search_form.cleaned_data[each]=='pending'):
                        filters.append(Q(**{'approval_status': None}))
                    if (search_form.cleaned_data[each] == 'assigned'):
                        filters.append(Q(**{'approval_status': 1}))
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    if (len(filters) > 0):
        request_list = ConsultancyRequest.objects.filter(reduce(operator.and_, filters)).filter(task__created_date__gt='2025-07-31')

    else:
        request_list = ConsultancyRequest.objects.filter(task__created_date__gt='2025-07-31')

    page_no = 1
    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    paginator = Paginator(request_list, no_of_items)

    try:
        request_list = paginator.page(page_no)

    except PageNotAnInteger:
        request_list = paginator.page(page_no)

    except EmptyPage:
        request_list = paginator.page(paginator.num_pages)

    context = {
        'request_list': request_list,
        'form': search_form,
    }

    return render(request, 'task_management/consultancy_requests.html', context)


def consultancy_request_approval(request, id):
    cr = ConsultancyRequest.objects.get(id=id)
    form = ConsultancyRequestApprovalForm(initial={'task': cr.task},instance=cr)

    context = {
        'form': form,
        'task': cr.task,
    }

    if (request.method == 'POST'):
        form = ConsultancyRequestApprovalForm(request.POST, initial={'task': cr.task}, instance=cr)
        if (form.is_valid()):
            req = form.save(commit=False)
            req.approved_by = request.user
            req.approved_at = datetime.datetime.now()
            req.approval_status = 1
            req.save()
            ConsultantTasks.objects.create(task=cr.task, consultant=req.consultant, assigned_by=request.user,
                                           created_at=datetime.datetime.now())
            #TODO: sms to consultant
            message = 'Consultancy Request Approved'
            context.update({'message': message})

    return render(request, 'task_management/consultancy_request_approval.html', context)


def task_comment(request, id):

    comment_list = Comment.objects.none()
    task_list = []

    if(request.user.profile.access_level < 3):
        task_list = Comment.objects.all().order_by('-created_date').values_list('task_id_id').distinct()

    elif(request.user.profile.access_level > 5):
        task_list = Task.objects.filter(supervisor=request.user).union(Task.objects.filter(task_executor=request.user)).values_list('id')
    else:
        task_list = Comment.objects.filter(task_id__division=request.user.profile.division).order_by('-created_date').values_list('task_id__id').distinct()

    comment_list = Comment.objects.filter(task_id__in=task_list).order_by('-created_date')

    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    paginator = Paginator(comment_list, no_of_items)

    try:
        comment_list = paginator.page(page_no)

    except PageNotAnInteger:
        comment_list = paginator.page(page_no)

    except EmptyPage:
        comment_list = paginator.page(paginator.num_pages)

    context = {
        'comment_list': comment_list
    }

    return render(request, 'task_management/task_comment.html', context)