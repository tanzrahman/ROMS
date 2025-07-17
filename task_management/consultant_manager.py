import threading
import datetime
import json
from django.core import paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.models import *
from system_log.models import *
from task_management.notify_users import send_notification, task_comment_notification
from task_management.system_list import systems as system_list
from task_management.forms import *
from task_management.milestone_handler import milestone_list
from task_management.milestone_handler import verify_milestones
import csv
from io import StringIO
from task_management.notify_users import send_task_list_notification,send_consultant_docreq_notification
from task_management.qa_handler import add_question_answer
from task_management.manage_tasks import edit_task, get_user,task_reassignment,task_list, task_suggestion, add_actual_start_date, add_lead_executor, add_actual_end_date
from task_management.qa_handler import add_question_answer,edit_answer,executor_feedback,supervisor_feedback, ongoing_executor_feedback

from time import sleep


def consultant_request_handler(request,menu=None,action=None,id=None):

    if(menu == 'task_list'):
        return consultant_tasklist_handler(request,action,id)
    if(menu == 'monitored_task_list'):
        return consultant_monitored_tasklist_handler(request,action,id)

    if(menu == 'task'):
        if(action =='open'):
            return consultant_task_open(request,action,id)
        if(action == 'participate'):
            return participate_task(request, action, id)
        if (action == 'feedback'):
            return task_feedback(request, action, id)
        if(action == 'add_comment'):
            return consultant_task_comment(request, action, id)
        if(action == 'view_es_feedback'):
            return view_es_feedback(request, id)
        if(action == 'delete_task'):
            return consultant_task_delete(request, action, id)

    if(menu == 'document_request'):
        return consultant_document_request(request, action,id)

    if(menu == 'discussion'):
            th = threading.Thread(target=update_consultant_lecture, args=(request.user,))
            th.start()
            return consultant_discussion_handler(request, action, id)

    total_task = []
    monitored_task = []
    total_task.append(Task.objects.all().count())
    monitored_task.append(ConsultantTasks.objects.filter(consultant=request.user).count())

    total_discussion = []
    participated_discussion = []
    feedback = []
    total_discussion.append(Lecture.objects.all().count())
    participated_discussion.append(ConsultantLecture.objects.filter(consultant=request.user).count())
    feedback.append(ConsultantLecture.objects.filter(consultant=request.user).exclude(review_report=None).count())

    divisions = []
    division_name = ['All Divisions']

    div = Task.objects.filter(division__isnull=False).values_list('division__division_name').distinct()
    for each in div:
        divisions.append(each[0])

    for each in divisions:
        total_task.append(Task.objects.filter(division__division_name=each).count())
        monitored_task.append(ConsultantTasks.objects.filter(consultant=request.user).filter(
            task__division__division_name=each).count())
        total_discussion.append(Lecture.objects.filter(target_division__division_name=each).count())
        participated_discussion.append(ConsultantLecture.objects.filter(consultant=request.user).filter(
            lecture__target_division__division_name=each).count())
        feedback.append(ConsultantLecture.objects.filter(consultant=request.user).filter(
            lecture__target_division__division_name=each).exclude(review_report=None).count())
        division_name.append(each)

    context = {
        'total_task': total_task,
        'monitored_task': monitored_task,
        'total_discussion': total_discussion,
        'participated_discussion': participated_discussion,
        'division_name': division_name,
        'feedback': feedback,
    }
    return render(request, 'consultant/consultant_chart.html', context)


def consultant_tasklist_handler(request, action, id):
    page_no = 1
    task_list = []
    search_summary = None

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = ConsultantTaskSearchForm(initial={'user': request.user})
    total_tasks = Task.objects.filter(percent_completed__lt=100).count()
    total_monthly_tasks = Task.objects.filter(planned_start_date__month=datetime.datetime.today().month).count()

    filters = []

    if (request.GET):
        search_form = ConsultantTaskSearchForm(request.GET, initial={'user': request.user})
        if (search_form.is_valid()):

            filters.append(Q(**{'percent_completed__lt':100}))
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
                if ('task_category' in each):
                    if (search_form.cleaned_data['task_category'][0] != ""):
                        filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                        continue
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    if (len(filters) > 0):
        task_list = Task.objects.filter(reduce(operator.and_, filters))
        search_summary = {
            'total_tasks': task_list.count(),
            'monthly_tasks': task_list.filter(planned_start_date__month=datetime.datetime.today().month).count()
        }
    else:
        task_list = Task.objects.filter(percent_completed__lt=100)

    # get feedback report
    total_feedback = TaskFeedBack.objects.filter(task__in=task_list)
    executor_feedback = ExecutorFeedBack.objects.filter(task__in=task_list)
    supervisor_feedback = SupervisorFeedBack.objects.filter(task__in=task_list)

    day_limit = datetime.datetime.today() - datetime.timedelta(days=3)
    older_than_3_tasks = task_list.filter(updated_date__lt=day_limit, taskfeedback__isnull=True)

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

    context = {'task_list': task_list, 'total_tasks': total_tasks, 'monthly_tasks': total_monthly_tasks}

    if (search_summary):
        context.update({
            'search_summary': search_summary
        })

    context.update({
        'form': search_form
    })

    return render(request, 'consultant/consultant_task_list.html', context)
    pass


def consultant_monitored_tasklist_handler(request, action, id):
    page_no = 1
    task_list = []
    search_summary = None

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    search_form = ConsultantTaskSearchForm(initial={'user': request.user})
    total_tasks = ConsultantTasks.objects.all().count()
    total_monthly_tasks = ConsultantTasks.objects.filter(task__planned_start_date__month=datetime.datetime.today().month).count()

    filters = []

    if (request.GET):
        search_form = ConsultantTaskSearchForm(request.GET, initial={'user': request.user})
        if (search_form.is_valid()):
            filters.append(Q(**{'consultant':request.user}))
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
                    filters.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('title' in each):
                    filters.append(Q(**{'task__title__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('supervisor' in each or 'task_executor' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if ('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if ('task_category' in each):
                    if (search_form.cleaned_data['task_category'][0] != ""):
                        filters.append(Q(**{'task__task_category__in': search_form.cleaned_data[each]}))
                        continue
                else:
                    filters.append(Q(**{each: search_form.cleaned_data[each]}))

    if (len(filters) > 0):
        task_list = ConsultantTasks.objects.filter(reduce(operator.and_, filters))
        search_summary = {
            'total_tasks': task_list.count(),
            'monthly_tasks': task_list.filter(task__planned_start_date__month=datetime.datetime.today().month).count()
        }
    else:
        task_list = ConsultantTasks.objects.filter(consultant=request.user)

    # # get feedback report
    # total_feedback = TaskFeedBack.objects.filter(task__in=task_list)
    # executor_feedback = ExecutorFeedBack.objects.filter(task__in=task_list)
    # supervisor_feedback = SupervisorFeedBack.objects.filter(task__in=task_list)
    #
    # day_limit = datetime.datetime.today() - datetime.timedelta(days=3)
    # older_than_3_tasks = task_list.filter(updated_date__lt=day_limit, taskfeedback__isnull=True)
    #
    # feedback_summary = {'total_feedback': total_feedback, 'executor_feedback': executor_feedback,
    #                     'supervisor_feedback': supervisor_feedback, 'no_feedback': older_than_3_tasks}

    no_of_items = 100
    paginator = Paginator(task_list, no_of_items)

    try:
        task_list = paginator.page(page_no)

    except PageNotAnInteger:
        task_list = paginator.page(page_no)

    except EmptyPage:
        task_list = paginator.page(paginator.num_pages)

    context = {'task_list': task_list, 'total_tasks': total_tasks, 'monthly_tasks': total_monthly_tasks}

    if (search_summary):
        context.update({
            'search_summary': search_summary
        })

    context.update({
        'form': search_form
    })

    return render(request, 'consultant/consultant_monitored_task_list.html', context)



def consultant_task_comment(request,action,id):
    task = Task.objects.get(id=id)
    form = ConsultantCommentForm(initial={'task_id': id})


    context = {'form': form}

    if(request.method == 'POST'):
        form = ConsultantCommentForm(request.POST,initial={'task_id': id})

        if(form.is_valid()):
            comment = form.save()
            comment.user = request.user
            comment.created_date = datetime.datetime.now()
            comment.save()
            msg = "Success"
            form = ConsultantCommentForm()
            context.update({
                'success':msg,
                'form':form
            })
            th = threading.Thread(target=task_comment_notification,args=(task, request.user))
            th.start()


    return render(request,'consultant/add_comment.html',context)
def consultant_task_open(request,action,id):
    task = Task.objects.get(id=id)
    supervisor_list = TaskSupervisorLink.objects.filter(task_id=task)
    executor_list = TaskExecutorLink.objects.filter(task_id=task)
    comment_list = Comment.objects.filter(task_id=task).order_by('-created_date')
    question_answer_list = QuestionsAnswers.objects.filter(task_id=task, answered_by=request.user)


    task_feedback = None
    if (TaskFeedBack.objects.filter(task=task).count() > 0):
        task_feedback = TaskFeedBack.objects.get(task=task)

    context = {
        'task': task,
        'comment_list': comment_list,
        'question_answer_list': question_answer_list,
        'task_feed_back': task_feedback,
        'supervisors': supervisor_list,
        'executors': executor_list,
    }
    return render(request, 'consultant/open_task.html', context)
def consultant_discussion_handler(request, action, id):
    if(action == 'list'):
        return all_discussion_list(request,action,id)
    if(action == 'open'):
        return open_discussion(request, id)
    if(action == 'participate'):
        return participate_lecture(request, id)
    if(action == 'feedback'):
        return discussion_feedback(request, id)
    if(action == 'view_feedback'):
        return view_feedback(request,id)
    if(action == 'edit_feedback'):
        return edit_feedback(request,id)
    if(action == 'my_list'):
        return consultant_participated_discussion_handler(request, action, id)
    return redirect('/')

def consultant_participated_discussion_handler(request, action, id):

    lect_list = ConsultantLecture.objects.filter(consultant=request.user).order_by('lecture__schedule').distinct()
    return render(request, 'consultant/participated_discussion_list.html', {'lectures': lect_list})

    return redirect('/')



def view_feedback(request,id):

    lect = Lecture.objects.get(id=id)
    cfb = ConsultantQA.objects.filter(consultant=request.user,lecture=lect)
    if(cfb.count()>0):
        cfb = cfb.first()
    else:
        cfb = None

    feedback = ConsultantQA.objects.get(lecture=lect)
    comment_list = Comment.objects.filter(consultant_qa=feedback).order_by('-created_date')

    context = {'lecture':lect, 'feedback':cfb, 'comment_list': comment_list}
    return render(request,'consultant/view_lecture_feedback.html',context)

def participate_lecture(request, id):
    lect = Lecture.objects.get(id=id)
    if (lect.other_participants.filter(username=request.user.username).count() < 1):
        ConsultantLecture.objects.create(lecture=lect, consultant=request.user,created_at=datetime.datetime.now())
        lect.other_participants.add(request.user)
        lect.save()
    return redirect('/consultant/discussion/list')


def discussion_feedback(request,id):

    lect = Lecture.objects.get(id=id)

    if (ConsultantQA.objects.filter(lecture=lect, consultant=request.user).count() > 0):
        return HttpResponse("You already given feedback on this lecture")

    init_params = {'lecture': lect, 'user': request.user}

    form = ConsultantQAForm(initial=init_params)

    context = {'form':form,'lecture':lect}

    if(request.method == 'POST'):
        form = ConsultantQAForm(request.POST,initial=init_params)
        msg = 'Submission has errors, please check'

        if(form.is_valid()):
            lect_fb = form.save()

            #set non-form values
            lect_fb.lecture = lect
            lect_fb.consultant = request.user
            lect_fb.created_at = datetime.datetime.now()

            #set form values
            best_participants = form.cleaned_data['qa3']
            improve_required = form.cleaned_data['qa9']
            for each in best_participants:
                lect_fb.qa3.add(each)

            for each in improve_required:
                lect_fb.qa9.add(each)
            lect_fb.save()
            msg = 'Successfully Submitted Feedback'
            form = ConsultantQAForm(initial=init_params)
            context.update({'success':msg})
        else:
            context.update({'error':msg})

        context.update({'form': form})

    return render(request,'consultant/lecture_feedback.html',context)

def open_discussion(request, id):

    lecture = Lecture.objects.get(id=id)
    sv_participants = User.objects.none()
    exec_participants = User.objects.none()
    for each in lecture.tasks.all():
        sv_participants |= each.supervisor.all()
        exec_participants |= each.task_executor.all()

    sv_participants = sv_participants.distinct()
    exec_participants = exec_participants.distinct()

    context = {'lecture': lecture, 'sv_participants': sv_participants, 'exec_participants': exec_participants}
    return render(request, 'consultant/open_lecture.html', context)


def participate_task(request, action, id):
    task = Task.objects.get(id=id)

    ConsultantTasks.objects.create(task=task,consultant=request.user,created_at=datetime.datetime.now())

    return redirect ('/consultant/monitored_task_list')

def task_feedback(request, action, id):
    task = Task.objects.get(id=id)
    print(id)
    tc_link = ConsultantTasks.objects.get(task=task, consultant=request.user)
    form = ConsultantTaskFeedback(instance=tc_link)

    feedback = ConsultantTasks.objects.get(task=task)
    comment_list = Comment.objects.filter(consultant_task_feedback=feedback).order_by('-created_date')

    context = {'form': form,'task':task, 'comment_list': comment_list}

    if (request.method == 'POST'):
        form = ConsultantTaskFeedback(request.POST,instance=tc_link)

        if (form.is_valid()):
            tfb = form.save()
            tfb.report_submitted_at = datetime.datetime.now()
            tfb.save()
            msg = "Success"
            form = ConsultantTaskFeedback()
            context.update({
                'success': msg,
                'form': form
            })

    return render(request, 'consultant/add_task_feedback.html', context)

def update_consultant_lecture(consultant):
    lectures = Lecture.objects.filter(other_participants=consultant)
    for each in lectures:
        if(ConsultantLecture.objects.filter(consultant=consultant,lecture=each).count()<1):
            #Consultant lecture item not created
            ConsultantLecture.objects.create(consultant=consultant,lecture=each,created_at=datetime.datetime.now())

def all_discussion_list(request,action,id):
    lect_list = Lecture.objects.all().order_by('schedule').distinct()
    form = LectureSearchForm()

    filter_list = []
    if (request.GET):
        form = LectureSearchForm(request.GET)

        if(form.is_valid()):
            for each in form.changed_data:
                if(each=='target_division'):
                    filter_list.append(Q(**{each:form.cleaned_data[each]}))
                if(each=='lecture_name'):
                    filter_list.append(Q(**{each+"__icontains": form.cleaned_data[each]}))
                if (each == 'lecture_category'):
                    filter_list.append(Q(**{each + "__icontains": form.cleaned_data[each]}))

    if(len(filter_list)>0):
        lect_list = Lecture.objects.filter(reduce(operator.and_, filter_list))
        
    context = {'lectures': lect_list, 'form':form}
    return render(request, 'consultant/discussion_list.html', context)

def edit_feedback(request,id):
    consultant_lecture = ConsultantQA.objects.get(id=id)
    init_params = {'lecture': consultant_lecture.lecture, 'user': consultant_lecture.consultant}
    form = ConsultantQAForm(instance=consultant_lecture,initial=init_params)

    context = {'form':form,'lecture':consultant_lecture.lecture}

    if(request.method == 'POST'):
        form = ConsultantQAForm(request.POST,instance=consultant_lecture,initial=init_params)
        if(form.is_valid()):
            form.save()
            msg = 'Successfully Updated Feedback'
            form = ConsultantQAForm(initial=init_params)
            context.update({'success':msg})
            context.update({'redirect':'/consultant/discussion/view_feedback/'+str(consultant_lecture.lecture.id)})

    return render(request,'consultant/lecture_feedback.html',context)


def view_es_feedback(request, id):
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




    context = {'feedback': task_feedback, 'exec_feedbacks': exec_feedbacks, 'sup_feedbacks': sup_feedbacks,
               'questions':questions, 'sup_questions':sup_questions}

    return render(request, 'consultant/view_task_es_feedback.html', context)


def consultant_task_delete(request,action,id):
    con_task = ConsultantTasks.objects.get(id=id)
    context = {'contask':con_task, 'task':con_task.task}

    if(request.method=='POST'):
        con_task.delete()
        context = {'success':'Succesffully removed task from your list'}

    return render(request,'consultant/delete_task.html',context)

def consultant_document_request(request, action,id):
    if(action == 'my_requests'):
        return view_my_requests(request)
    if(action == 'create'):
        return create_reqeust(request,id)


def view_my_requests(request):
    my_requests = DocumentRequest.objects.filter(requested_by=request.user).order_by('-requested_at')
    return render(request, 'consultant/my_document_requests.html', {'my_requests': my_requests})


def create_reqeust(request, task_id=None):
    task = Task.objects.get(id=task_id)
    form = DocumentReqeustForm(initial={'task_id': task_id})
    curr_day = datetime.date.today()
    todays_req = DocumentRequest.objects.filter(requested_by=request.user,requested_at__gte=curr_day)
    if(todays_req.count() >= 15):
        return HttpResponse("You Cannot Request more than 15 documents a day")

    context = {'form': form, 'task': task}
    if (request.method == 'POST'):
        form = DocumentReqeustForm(request.POST, initial={'task_id': task_id})
        if (form.is_valid()):
            doc_request = form.save()
            doc_request.approval_level = 1
            doc_request.requested_by = request.user
            doc_request.requested_at = datetime.datetime.now()
            doc_request.save()
            context.update({'success': 'Successfully Created Request'})
            send_consultant_docreq_notification(doc_request)
        context.update({'form': form})

    return render(request, 'consultant/document_request.html', context)