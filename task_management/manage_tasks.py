import datetime
import threading
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.forms import *
import csv
from io import StringIO
from task_management.notify_users import send_reassign_notification, send_consultant_task_notification
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from system_log.models import TaskLog
track_dict = {}
def get_user(email,phone,division,file,is_supervisor=False):

    user = None
    if(email!=""):
        if(User.objects.filter(email=email).count()<1):
            #user doesnt exists, create user
            user = User.objects.create_user(username=email,email=email,password='vver1200@RNPP')

            if(phone[0]!='0'):
                user.profile.phone = "0"+phone
            else:
                user.profile.phone = phone
            user.profile.division = division

            if(is_supervisor):
                user.profile.is_supervisor = True
                user.profile.is_executor = False
                user.profile.grade = 9
                user.profile.access_level = 9
            else:
                user.profile.is_supervisor = False
                user.profile.is_executor = True
                user.profile.grade = 10
                user.profile.access_level = 10

            if(not 'rooppurnpp' in email):
                #if user dosent have any official mail, mark inactive
                user.is_active = False

            user.profile.save()
            track_dict.update({email:"Y"})

            msg = "{},{},{}\n".format(email,phone, division)
            file.write(msg)
        else:
            user = User.objects.get(email=email)
            if(track_dict.get(email)==None):
                track_dict.update({email: "Y"})
                user.profile.phone = "0"+phone
                if(is_supervisor):
                    user.profile.is_supervisor = True
                if(not is_supervisor):
                    user.profile.is_executor = True
                user.profile.save()
    return user
def edit_task(request,task_id):

    if (request.user.profile.access_level > 4):
        if(not request.user.profile.is_supervisor):
            return HttpResponse("You Dont Have The Permission to Assign a new Task")
    initial = {}

    if(request.user.profile.access_level > 2):
        initial.update({
            'division': request.user.profile.division
        })


    initial.update({
        'creating_user': request.user
    })

    task = Task.objects.get(id=task_id)

    if(request.user.profile.access_level >1):
        if (request.user.profile.division != task.division):
            return HttpResponse("You Cannot Change Tasks from Other division")

    if(request.method == 'GET'):
        edit_task_form = TaskEditForm(initial=initial,instance=task)

        context = {'form': edit_task_form}

        return render(request, 'task_management/edit_task.html', context)

    if request.method == 'POST':
        form = TaskEditForm(request.POST,initial=initial,instance=task)

        old_sup = task.supervisor.all()
        old_exc = task.task_executor.all()

        removed_sup = []    #to send them notif
        new_added_sup =  []  #to send them notif

        removed_exc = []    #to send them notif
        new_added_exc = []  #to send them notif

        if form.is_valid():
            f_task = form.save(commit=False)

            f_task.updated_date = datetime.date.today()

            task_id = f_task.id
            new_sup = form.cleaned_data['supervisor']
            new_exec = form.cleaned_data['task_executor']

            removed_sup = set(old_sup)- set(new_sup)
            new_added_sup = set(new_sup)-set(old_sup)

            removed_exc = set(old_exc)-set(new_exec)
            new_added_exc = set(new_exec)-set(old_exc)

            removed_sup_str = ""
            removed_exc_str = ""
            added_sup_str = ""
            added_exc_str = ""
            for each in removed_sup:
                f_task.status = 'A'
                removed_sup_str = removed_sup_str + str(each) +", "
                f_task.supervisor.remove(each)  #remove old supervisors

            for each in new_added_sup:
                f_task.status = 'A'
                added_sup_str = added_sup_str + str(each) + ", "
                f_task.supervisor.add(each)  #add old supervisors


            for each in removed_exc:
                f_task.status = 'A'
                removed_exc_str = removed_exc_str + str(each) + ", "
                f_task.task_executor.remove(each)   #remove old exec

            for each in new_added_exc:
                f_task.status = 'A'
                added_exc_str = added_exc_str + str(each) + ", "
                f_task.task_executor.add(each)  #add new execs

            if('lead_executor' in form.changed_data):
                f_task.lead_executor = form.cleaned_data['lead_executor']
            f_task.save()

            notifiyer = threading.Thread(target=send_reassign_notification, args=(task_id,removed_sup,new_added_sup,removed_exc,new_added_exc))
            notifiyer.start()

            curr_time = datetime.datetime.now()
            TaskLog.objects.create(changed_by=request.user, task=task,added_supervisor=added_sup_str,
                                   added_executor=added_exc_str, removed_executor=removed_exc_str,created_at=curr_time,
                                   removed_supervisor=removed_sup_str,ip=request.META['REMOTE_ADDR'])

            add_task_form = TaskEditForm()
            context = {'form': add_task_form,'success':'success','task':task_id}

            return render(request, 'task_management/edit_task.html', context)

    else:
        HttpResponse ("NOT ALLOWED")


def task_reassignment(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")
        count = 0
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
                supervisor_1_email = row[8].strip().replace(' ', '').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ', '')

                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ', '').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ', '').lower()

                division = row[15].strip()
                division_obj = None

                division_obj = Division.objects.get(division_name=division)

                supervisor_1 = get_user(supervisor_1_email, supervisor_1_phone, division_obj, new_user,
                                        is_supervisor=True)

                supervisor_2 = get_user(supervisor_2_email, supervisor_2_phone, division_obj, new_user,
                                        is_supervisor=True)

                executor_1 = get_user(executor_1_email, executor_1_phone, division_obj, new_user,
                                      is_supervisor=False)
                executor_2 = get_user(executor_2_email, executor_2_phone, division_obj, new_user,
                                      is_supervisor=False)

                new_task = None
                if(Task.objects.filter(milestone_id=milestone_id,division=division_obj).count()>0):
                    new_task =Task.objects.get(milestone_id=milestone_id,division=division_obj)
                else:
                    facility_filter = Facility.objects.filter(kks_code=facility_kks)
                    if (facility_filter.count() < 1):
                        facilty_obj = Facility.objects.create(kks_code=facility_kks, name=facility_kks)
                    else:
                        facilty_obj = facility_filter.first()

                    system_obj = None
                    sub_system_obj = None
                    if (system != ""):
                        if (System.objects.filter(name=system).count() < 1):
                            system_obj = System.objects.create(name=system)
                    if (sub_sys != ""):
                        if (SubSystem.objects.filter(name=sub_sys).count() < 1):
                            sub_system_obj = SubSystem.objects.create(name=sub_sys)
                            if (system_obj):
                                sub_system_obj.system = system_obj
                                sub_system_obj.save()
                    milestone_obj = Milestone.objects.get(milestone_id=milestone_id)
                    new_task = Task.objects.create(task_id=milestone_obj.task_id, milestone_id=milestone_obj.milestone_id,
                                    relevant_kks_codes=facilty_obj.kks_code, title=milestone_obj.title,
                                    description=milestone_obj.title,planned_start_date=milestone_obj.start_date,
                                    planned_end_date=milestone_obj.end_date,created_date=curr_date,task_created_by=supervisor_1,
                                    facility=facilty_obj, stage=stage,division=division_obj,
                                    is_active=True,status='N',system=system_obj,subsystem=sub_system_obj)
                    new_task.save()

                for each in new_task.task_executor.all():
                    new_task.task_executor.remove(each)

                for each in new_task.supervisor.all():
                    new_task.supervisor.remove(each)

                new_task.supervisor.add(supervisor_1)
                if (supervisor_2):
                    new_task.supervisor.add(supervisor_2)

                new_task.task_executor.add(executor_1)
                if (executor_2):
                    new_task.task_executor.add(executor_2)

                new_task.status = 'N'
                new_task.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id, e.__str__())
                print(msg)
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")

def task_list(request):

    page_no = 1
    task_list = []
    search_summary = None

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = AllTaskSearchForm(initial={'user':request.user})
    total_tasks = Task.objects.filter(percent_completed__lt=100).count()
    total_monthly_tasks = Task.objects.filter(planned_start_date__month=datetime.datetime.today().month).count()

    filters = []

    if (request.GET):
        search_form = AllTaskSearchForm(request.GET,initial={'user':request.user})
        if (search_form.is_valid()):
            #filters.append(Q(**{'percent_completed__lt': 100}))
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
                    continue
                if ('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if ('shop' in each):
                    filters.append(Q(**{"dept_id__in": search_form.cleaned_data[each]}))
                    continue
                if('task_category' in each):
                    if(search_form.cleaned_data['task_category'][0]!=""):
                        filters.append(Q(**{each+'__in': search_form.cleaned_data[each]}))
                        continue
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))


    if(request.user.profile.access_level>=4):
        filters.append(Q(**{'division':request.user.profile.division}))

    if (len(filters) > 0):
        task_list = Task.objects.filter(reduce(operator.and_, filters))
        search_summary= {
            'total_tasks':task_list.count(),
            'monthly_tasks':task_list.filter(planned_start_date__month=datetime.datetime.today().month).count()
        }
    else:
        task_list = Task.objects.filter(percent_completed__lt=100)

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

    #TODO: if download as excel is requested, return csv
    if(request.GET.get('download')):
        if(request.GET.get('download')=='excel'):
            print("Send CSV report")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="task_report.csv"'
            writer = csv.writer(response)
            writer.writerow(["Milestone ID","Task ID","Title","Progress (%)","Division","Department","Category",	"Supervisor","Executor","System","SubSystem","Facility","Planned start","Planned end","Actual start","Actual end"])
            for each in task_list:
                row = []
                row.append(each.milestone_id)
                row.append(each.task_id)
                row.append(each.title)
                row.append(each.percent_completed)
                row.append(each.division)
                row.append(each.dept_id)
                row.append(each.task_category)
                supervisors = [str(each)+";" for each in each.supervisor_list()]
                row.append(supervisors)
                executors = [str(each)+";" for each in each.executor_list()]
                row.append(executors)
                row.append(each.system)
                row.append(each.subsystem)
                row.append(each.facility)
                row.append(each.planned_start_date)
                row.append(each.planned_end_date)
                row.append(each.actual_start_date)
                row.append(each.actual_end_date)
                writer.writerow(row)
            return response

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
    return render(request,'task_management/all_task_list.html', context)


def started_task_list(request):

    page_no = 1
    task_list = []
    search_summary = None

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = AllTaskSearchForm(initial={'user':request.user})
    total_tasks = Task.objects.filter(percent_completed__lt=100).exclude(actual_start_date=None).count()
    total_monthly_tasks = Task.objects.filter(planned_start_date__month=datetime.datetime.today().month).exclude(actual_start_date=None).count()

    filters = []

    if (request.GET):
        search_form = AllTaskSearchForm(request.GET,initial={'user':request.user})
        if (search_form.is_valid()):
            filters.append(Q(**{'percent_completed__lt': 100}))
            #filters.append(Q(**{'actual_start_date_isnull': False}))
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
                    continue
                if ('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if ('shop' in each):
                    filters.append(Q(**{'dept_id__in': search_form.cleaned_data[each]}))
                    continue
                if('task_category' in each):
                    if(search_form.cleaned_data['task_category'][0]!=""):
                        filters.append(Q(**{each+'__in': search_form.cleaned_data[each]}))
                        continue
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))


    if(request.user.profile.access_level>=4):
        filters.append(Q(**{'division':request.user.profile.division}))

    if (len(filters) > 0):
        task_list = Task.objects.filter(reduce(operator.and_, filters)).exclude(actual_start_date=None)
        search_summary= {
            'total_tasks':task_list.count(),
            'monthly_tasks':task_list.filter(planned_start_date__month=datetime.datetime.today().month).count()
        }
    else:
        task_list = Task.objects.filter(percent_completed__lt=100).exclude(actual_start_date=None)

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

    # context.update({
    #     'feedback_summary': feedback_summary
    # })
    if(request.user.profile.access_level<=4):
        context.update({'user_can_reassign_task':True})

    return render(request,'task_management/started_task_list.html', context)

def task_suggestion(request,substr):
    tasks = Task.objects.filter(milestone_id__icontains=substr.upper())[:50]
    mids = tasks.values_list('id','milestone_id')

    return JsonResponse(list(mids),safe=False)


def add_actual_start_date(request, task_id):
    task = Task.objects.get(id=int(task_id))
    form = AddActualStartDateForm(initial={'user': request.user, 'task_id': task_id})

    if(request.method == 'GET'):
        return render(request,'task_management/add_actual_start_date.html', {'form': form, 'task': task})

    if(request.method == 'POST'):
        form = AddActualStartDateForm(request.POST, initial={'user': request.user, 'task_id': task_id})
        if(form.is_valid()):
            add_actual_start_date = form.cleaned_data['add_actual_start_date']
            task.actual_start_date = add_actual_start_date
            task.save()
            # todo: Notification mailer implementation
            message = "Successfully actual start date added"

        return render(request,'task_management/add_actual_start_date.html', {'form': form, 'task': task, 'message' : message})


def add_actual_end_date(request, task_id):
    task = Task.objects.get(id=int(task_id))
    form = AddActualEndDateForm(initial={'user': request.user, 'task_id': task_id})

    if(request.method == 'GET'):
        return render(request,'task_management/add_actual_end_date.html', {'form': form, 'task': task})

    if(request.method == 'POST'):
        form = AddActualEndDateForm(request.POST, initial={'user': request.user, 'task_id': task_id})
        if(form.is_valid()):
            add_actual_end_date = form.cleaned_data['add_actual_end_date']
            task.actual_end_date = add_actual_end_date
            if(add_actual_end_date < task.actual_start_date):
                message = "Actual end date should be greater than actual start date"
            else:
                task.save()
                # todo: Notification mailer implementation
                message = "Successfully actual end date added"

        return render(request,'task_management/add_actual_end_date.html', {'form': form, 'task': task, 'message' : message})


def add_lead_executor(request,id):

    if(request.GET.get('lexc')):
        task = Task.objects.get(id=id)
        user_id = request.GET.get('lexc')
        user = User.objects.get(id=user_id)
        task.lead_executor = user
        task.save()
        url = '/task_management/open_task/'+str(id)
        return redirect(url)
    else:
        HttpResponse("Error, Try Again Later")
    pass

def add_task_consultant(request,id):
    task = Task.objects.get(id=id)
    form = LectureAddConsultant()
    context = {'task': task, 'form':form}

    if(request.method == 'POST'):
        form = LectureAddConsultant(request.POST)
        if(form.is_valid()):
            con = form.cleaned_data['consultant']
            ConsultantTasks.objects.create(task=task,consultant=con,assigned_by=request.user,created_at=datetime.datetime.now())
            th = threading.Thread(target=send_consultant_task_notification,args=(task.id,con))
            th.start()
            context.update({'msg':'Consultant Successfully Added'})
    return render(request,'task_management/add_consultant_to_task.html',context)


def consultant_task_feedback_add_comment(request, id):
    con_qa = ConsultantTasks.objects.get(id=id)
    init_param = {'consultant_task':con_qa}
    form = ConsultantTaskFeedbackCommentForm(initial=init_param)
    context = {'form': form}
    if(request.method == 'POST'):
        form = ConsultantTaskFeedbackCommentForm(request.POST, initial=init_param)
        if(form.is_valid()):
            comment = form.save()
            comment.user = request.user
            comment.created_date = datetime.datetime.now()
            comment.save()
            message = "Comment Added Successfully"
            context.update({'message':message})
    return render(request,'task_management/add_comment.html', context)

def request_consultancy(request,id):
    task = Task.objects.get(id=id)
    init_param = {'task':task}
    form = ConsultancyRequestForm(initial=init_param)
    context = {'task': task, 'form': form}

    if(request.method == 'POST'):
        form = ConsultancyRequestForm(request.POST, initial=init_param)
        if(form.is_valid()):
            con_req = form.save(commit=False)
            con_req.requested_by = request.user
            con_req.created_at = datetime.datetime.now()
            con_req.save()
            msg = 'Successfully Submitted Request'
            context.update({'msg':msg})

    return render(request,'task_management/request_add_consultant_to_task.html',context)


def add_task_percentage(request, id):

    task = Task.objects.get(id=id)
    initial = {'percent_completed': task.percent_completed}
    form = AddTaskPercentageForm(initial=initial)
    context = {'task': task, 'form': form}

    if(request.method == 'POST'):
        form = AddTaskPercentageForm(request.POST, initial=initial, instance=task)
        if(form.is_valid()):
            task_percentage = form.save(commit=False)
            task_percentage.updated_by = request.user
            task_percentage.save()
            context.update({'message': 'Task Completion Status Successfully Updated'})
    return render(request, 'task_management/add_task_percentage.html', context)

def update_saw_level2_schedule(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("not_found_tasks.txt", "w")

        for row in reader:
            try:
                job_id = row[0]
                planned_start = row[1]
                planned_end = row[2]

                tasks = Task.objects.filter(task_id=job_id,task_category="SAW")

                if(tasks.count()>0):
                    print("Process")
                    if(tasks.count()>1):
                        msg = str(job_id) + ", " + str(planned_start) + ", " + str(planned_end) + ", DUPLICATE FOUND\n"
                        failed.write(msg)
                    tasks.update(planned_start_date=planned_start,planned_end_date=planned_end)

                else:
                    msg = str(job_id)+", "+str(planned_start)+", "+str(planned_end)+", NOT FOUND\n"
                    failed.write(msg)



            except Exception as e:
                print(e.__str__())


        failed.close()

        return HttpResponse("Task Dates Updated Done")



def upload_operational_document(request):
    if(request.method == 'GET'):
        return render(request,'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        task_category = 'DocumentReview'
        if(request.GET.get('task_category')):
            task_category = request.GET.get('task_category')

        count = 0
        new_email = {}
        curr_date = datetime.date.today()
        start_date = None
        end_date = None

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
                milestone_id = row[2].strip()
                job_id = row[2].strip()
                title = row[3].strip()
                division = row[4].strip()
                dept_code = row[5].strip().upper()
                supervisor_1_email = row[6].strip().replace(' ','').lower()
                executor_1_email = row[7].strip().replace(' ','').lower()

                division_obj = None
                dept_obj = None
                start_date = row[8].strip()
                end_date = row[9].strip()

                division_obj = Division.objects.filter(division_name=division).first()
                if(dept_code != ""):
                    dept_obj = DepartmentShop.objects.get(dept_code=dept_code)




                #if task with this milestone already created, ignore it
                if(Task.objects.filter(task_id=milestone_id).count()>0):
                    print("Document ID  Already Created")
                    msg = "Document already created with id, {}\n".format(milestone_id)
                    failed.write(msg)
                    continue

                supervisor_1 = User.objects.get(email=supervisor_1_email)

                executor_1 = User.objects.get(email=executor_1_email)

                new_task_obj = Task(task_id=job_id, milestone_id=milestone_id, title=title,
                                description=title, planned_start_date=start_date, dept_id=dept_obj,
                                planned_end_date=end_date, created_date=curr_date, percent_completed=0,
                                task_created_by=supervisor_1, division=division_obj, task_category=task_category,
                                is_active=True, status='N')
                new_task_obj.save()
                new_task_obj.supervisor.add(supervisor_1)

                new_task_obj.task_executor.add(executor_1)
                new_task_obj.save()

            except Exception as e:
                msg = "Failed, {}, {}\n".format(milestone_id,e.__str__())
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")