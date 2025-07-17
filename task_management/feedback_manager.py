import datetime

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from functools import reduce
import operator

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Count
from task_management.models import TaskFeedBack, ExecutorFeedBack, SupervisorFeedBack
from task_management.models import Task, QuestionsAnswers, Questions, Division, File
from task_management.forms import FeedbackSearchForm
from manpower.models import Profile, User
from task_management.ftp_handler import FILETYPE, fetch_file

def feedback_handler(request, action, id=None):
    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')
    if (action == 'show_all'):
        return show_all(request, id)
    if (action == 'open'):
        return open_feedback(request, id)
    if(action == 'send_msg'):
        return send_msg(request, id)
    if(action == "viewfile"):
        return view_file(request,id)
    if(action == 'executor_feedbacks'):
        return executor_feedbacks_handler(request, id)
    if(action == 'executor_specific_feedbacks'):
        return executor_specific_feedbacks(request, id)


def show_all(request, id=None):

    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    feedback_list = TaskFeedBack.objects.all().order_by('-created_at','task__division')

    # task_ids = TaskFeedBack.objects.all().values_list('task__id', flat=True)
    # tasks = Task.objects.filter(id__in=task_ids)

    search_form = FeedbackSearchForm(request.GET)

    search_filters = []
    if(search_form.is_valid()):
        for each in search_form.changed_data:
            if(each == 'division'):
                search_filters.append(Q(**{'task__division': search_form.cleaned_data[each]}))
            elif(each == 'task'):
                search_filters.append(Q(**{'task': search_form.cleaned_data[each]}))
            elif(each == 'task_category'):
                search_filters.append(Q(**{'task__task_category': search_form.cleaned_data[each]}))
            elif(each == 'feedback_from'):
                search_filters.append(Q(**{'created_at__gte': search_form.cleaned_data[each]}))
            elif (each == 'feedback_from'):
                search_filters.append(Q(**{'created_at__gte': search_form.cleaned_data[each]}))
            elif (each == 'feedback_to'):
                search_filters.append(Q(**{'created_at__lte': search_form.cleaned_data[each]}))
            elif (each == 'task_from'):
                search_filters.append(Q(**{'task__planned_start_date__gte': search_form.cleaned_data[each]}))
            elif (each == 'task_to'):
                search_filters.append(Q(**{'task__planned_end_date__lte': search_form.cleaned_data[each]}))

    if(len(search_filters)>0):
        feedback_list = TaskFeedBack.objects.filter(reduce(operator.and_, search_filters)).order_by('-created_at')

    divs = Division.objects.all()
    div_summary = []

    for each in divs:
        fbs = TaskFeedBack.objects.filter(task__division=each)
        fb_count = fbs.count()
        fb_today = fbs.filter(created_at__gte = datetime.date.today(), created_at__lte=datetime.datetime.today()).count()
        fb_3days = fbs.filter(created_at__gte=datetime.datetime.today() - datetime.timedelta(days=3),created_at__lte=datetime.datetime.today() ).count()
        fb_7days = fbs.filter(created_at__gte=datetime.datetime.today() - datetime.timedelta(days=7),
                              created_at__lte=datetime.datetime.today()).count()
        if(fb_count > 0):
            div_summary.append((each, fb_count,fb_today,fb_3days,fb_7days))


    no_of_items = 100
    paginator = Paginator(feedback_list, no_of_items)

    try:
        feedback_list = paginator.page(page_no)

    except PageNotAnInteger:
        feedback_list = paginator.page(page_no)

    except EmptyPage:
        feedback_list = paginator.page(paginator.num_pages)

    context = {'feedback_list':feedback_list, 'div_summary':div_summary,'form':search_form}
    return render(request, 'task_management/show_feedback_report.html', context)


def open_feedback(request, id):
    task_feedback = TaskFeedBack.objects.get(id=id)

    sup_feedback = task_feedback.supervisor_feedback.all()
    exec_feedback = task_feedback.executor_feedback.all()

    exec_feedbacks = []
    questions = Questions.objects.filter(employee_category='executor',task_state='pre_start').order_by('priority')
    for q in questions:
        fb = [(q.que,q.id)]
        fb_id = None
        for each in exec_feedback:
            #answers = each.answers.order_by('task_question__priority')
            answer = each.answers.filter(task_question__priority=q.priority).first()
            fb.append((answer,each.id))
        exec_feedbacks.append(fb)

    sup_feedbacks = []
    sup_questions = Questions.objects.filter(employee_category='supervisor',task_state='pre_start').order_by('priority')
    for q in sup_questions:
        fb = [q.que]
        for each in sup_feedback:
            # answers = each.answers.order_by('task_question__priority')
            answer = each.answers.filter(task_question__priority=q.priority).first()
            fb.append(answer)

        feed_back_str = ""
        if(len(fb)>1):
            feed_back_str = "<b>{}</b> feedback <br>for: <b>{}</b>".format(each.supervisor, each.executor_feedback.executor)
        sup_feedbacks.append((fb,feed_back_str))

    print(feed_back_str)



    # for each in sup_feedback:
    #     answers = each.answers.order_by('task_question__priority')
    #     feed_back = []
    #     feed_back_str = "{} feedback for: {}".format(each.supervisor, each.executor_feedback.executor)
    #     feed_back.append(feed_back_str)
    #     for i in range(0, len(sup_questions)):
    #         found = False
    #         for answer in answers:
    #             if (answer.task_question.priority == sup_questions[i].priority):
    #                 found = True
    #                 feed_back.append(answer)
    #         if (not found):
    #             feed_back.append("")
    #     sup_feedbacks.append(feed_back)



    context = {'feedback': task_feedback, 'exec_feedbacks': exec_feedbacks, 'sup_feedbacks': sup_feedbacks,
               'questions':questions, 'sup_questions':sup_questions}

    return render(request, 'task_management/show_feedback_details.html', context)


def send_msg(request, id):
    ex_fb = None
    sup_fb = None
    task_fb = None

    if(request.GET.get('ex_fb')):
        ex_fb = request.GET.get('ex_fb')
    if(request.GET.get('sup_fb')):
        sup_fb = request.GET.get('sup_fb')

    task_fb = TaskFeedBack.objects.get(id=id)

    msg_body = "msg_body=Mr. {} Task: {}"

    if(ex_fb):
        efb = ExecutorFeedBack.objects.get(id=ex_fb)
        msg_body = msg_body.format(efb.executor.first_name,task_fb.task)

    users = []
    for exfb in task_fb.executor_feedback.all():
        users.append(exfb.executor.id)

    for supfb in task_fb.supervisor_feedback.all():
        users.append(supfb.supervisor.id)

    higher_users = User.objects.filter(profile__division=task_fb.task.division,
                                       profile__designation__in=["Shop Manager", "Deputy Shop Manager"])
    for each in higher_users:
        users.append(each.id)

    url_str = ""
    for each in users:
        url_str = url_str + "user="+str(each)+"&"

    url = "/group_sms?"+url_str+msg_body
    return redirect(url)

def view_file(request,hash):
    file_object = File.objects.get(hash=hash)
    file = fetch_file(request, file_object.server_loc)

    response = HttpResponse(file, content_type=FILETYPE[file_object.file_type])
    response['Content-Disposition'] = 'inline; filename="' + file_object.file_name + '"'
    return response

def executor_feedbacks_handler(request, id):
    context = {}

    if(request.GET.get('send_msg')):
        uid = request.GET.get('userid')
        if (request.GET.get('tasks')):
            if (request.GET.get('tasks') == 'no_feedback'):
                return send_msg_no_exec_feedback(request, id)

        user = User.objects.get(id=uid)
        msg_body = request.GET.get('msg_body')
        efb_count = ExecutorFeedBack.objects.filter(executor=uid).count()
        task_count = Task.objects.filter(task_executor=uid).count()
        if(request.GET.get('assigned_only')):
            task_count = Task.objects.filter(task_executor=uid,status__in=['A','1']).count()

        uname = user.first_name
        if(not user.first_name):
            uname = user.email.split('@')[0]

        msg_body = "msg_body=Mr.{}, Feedback: {} out of {} as Executor".format(uname,efb_count, task_count)
        user_str = "user={}".format(uid)
        division = "receiver_division={}".format(user.profile.division.div_id)
        url = "/group_sms?" + user_str + '&' + msg_body + '&' + division
        return redirect(url)

    executors_feedbacks = ExecutorFeedBack.objects.values_list('executor', 'executor__email',
        'executor__profile__division__division_name','executor__profile__department__dept_name').annotate(
        feedback_count=Count('executor__email')).distinct().order_by('-feedback_count')

    feedback_executors = ExecutorFeedBack.objects.values_list('executor').annotate().distinct()

    no_feedback_users = []

    executors_all = User.objects.filter(profile__is_executor=True)
    executors_all = executors_all.exclude(id__in=feedback_executors)
    assigned_tasks = Task.objects.filter(status__in=['A','1'])

    for each in executors_all:
        task_count = assigned_tasks.filter(task_executor=each).count()
        if(task_count>0):
            no_feedback_users.append((each.id,each.email,each.profile.division,task_count))

    sorted_no_feedback_users = sorted(no_feedback_users,key=operator.itemgetter(3), reverse = True)
    context.update({
        'executors_feedbacks':executors_feedbacks,
        'no_feedback_count':len(no_feedback_users),
        'no_feedback_users':sorted_no_feedback_users,
        'assigned_task':assigned_tasks.count()
    })
    return render(request,'task_management/executor_feedbacks_report.html',context)


def executor_specific_feedbacks(request, id):
    user = User.objects.get(id=id)
    efb = TaskFeedBack.objects.filter(executor_feedback__executor=user).order_by('-created_at')

    context = {'feedback_list':efb, 'user':user}

    return render(request,'task_management/exec_specific_feedback_report.html',context)


def send_msg_no_exec_feedback(request,id):

    feedback_executors = ExecutorFeedBack.objects.values_list('executor').annotate().distinct()

    no_feedback_users = []

    executors_all = User.objects.filter(profile__is_executor=True)
    executors_all = executors_all.exclude(id__in=feedback_executors)
    assigned_tasks = Task.objects.filter(status__in=['A', '1'])

    user_str = ''
    for each in executors_all:
        task_count = assigned_tasks.filter(task_executor=each).count()
        if (task_count > 0):
            user_str = user_str + "user={}&".format(each.id)
    print(user_str)
    msg_body = "msg_body=Dear Executors, you have no feedbacks yet"

    msg_send_url = "/group_sms?"+user_str+"&"+msg_body

    return redirect(msg_send_url)
