
import datetime
import operator
import threading
from functools import reduce

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from time import sleep
from manpower.models import Division
from task_management.models import Task, User, DocumentRequest, Lecture, ConsultantLecture, ConsultantQA, ConsultantTasks
from task_management.forms import LectureScheduleForm, LectureSearchForm, LectureAddConsultant, ConsultantLectureFeedbackComment, ConsultantTaskFeedbackCommentForm
from task_management.notify_users import send_notification,mail_and_send_sms, send_consultant_discussion_notification
def lecture_request_handler(request,action,id=None):
    if (request.user.is_anonymous):
        return redirect('/')

    if(action == 'create'):
        return lecture_create(request,action,id)
    if(action == 'lecture_list'):
        return lecture_list(request,action,id)
    if(action == 'open'):
        return open_lecture(request, action, id)
    if(action == 'notify'):
        return notify_lecture_schedule(request, action, id)
    if(action == 'edit'):
        return edit_lecture(request, action, id)
    if(action == 'send_msg'):
        return send_msg(request,id)
    if(action == 'add_consultant'):
        return add_consultant(request,action,id)
    if(action == 'consultant_qa_add_comment'):
        return consultant_qa_add_comment(request,action,id)
def lecture_create(request,action,id=None):
    form = LectureScheduleForm()
    init_param = {}
    if(request.GET.get('div')):
        div = Division.objects.get(div_id=request.GET.get('div'))
        init_param.update({'division': div})
    if(request.GET.get('keyword')):
        keyword = request.GET.get('keyword')
        init_param.update({'keyword': keyword})
    form = LectureScheduleForm(initial=init_param)
    context = {'form': form}
    if(request.method == 'POST'):
        form = LectureScheduleForm(request.POST, initial=init_param)
        if(form.is_valid()):
            lect = form.save()
            lect.approval_level = 0
            lect.notified_users = 0
            task_list = form.cleaned_data['tasks']
            other_presenter = form.cleaned_data['other_presenter']
            for each in task_list:
                lect.tasks.add(each)
            for each in other_presenter:
                lect.other_presenter.add(each)
            lect.save()
            context.update({'success': 'Successfully Created Lecture Schedule'})
            form = LectureScheduleForm()
            context.update({'form': form})


    return render(request, 'task_management/create_lecture.html', context)


def lecture_list(request,action,id):
    lect_list = Lecture.objects.none()
    lecture_divs = Lecture.objects.all().values_list('target_division', flat=True).distinct()
    lecture_divs = Division.objects.filter(div_id__in=lecture_divs)
    if(request.user.profile.access_level>5 and not request.user.has_perm('task_management.add_lecture')):
        lect_list_e = Lecture.objects.filter(tasks__task_executor=request.user,notified_users__gt=0).distinct().order_by('schedule')
        lect_list_s = Lecture.objects.filter(tasks__supervisor=request.user).distinct().order_by('schedule')

        lect_list = lect_list_e | lect_list_s

    else:
        if(request.user.profile.access_level < 4):
            lect_list = Lecture.objects.all().order_by('schedule').distinct()
            form = LectureSearchForm()

            filter_list = []
            if (request.GET):
                form = LectureSearchForm(request.GET)

                if (form.is_valid()):
                    for each in form.changed_data:
                        if (each == 'target_division'):
                            filter_list.append(Q(**{each: form.cleaned_data[each]}))
                        if (each == 'lecture_name'):
                            filter_list.append(Q(**{each + "__icontains": form.cleaned_data[each]}))
                        if (each == 'lecture_category'):
                            filter_list.append(Q(**{each + "__icontains": form.cleaned_data[each]}))

            if (len(filter_list) > 0):
                lect_list = Lecture.objects.filter(reduce(operator.and_, filter_list))

            context = {'lectures': lect_list, 'form': form,'lecture_divs':lecture_divs}
            return render(request, 'task_management/lecture_list.html', context)

        if(request.user.profile.access_level>=4):
            lect_list = Lecture.objects.filter(target_division=request.user.profile.division).order_by('schedule').distinct()

    lect_lead_p = Lecture.objects.filter(lead_presenter=request.user).distinct()
    lect_p = Lecture.objects.filter(other_presenter=request.user).distinct()
    lect_list = lect_list | lect_p | lect_lead_p


    return render(request, 'task_management/lecture_list.html', {'lectures': lect_list})

def open_lecture(request, action, id):

    lecture = Lecture.objects.get(id=id)
    sv_participants = User.objects.none()
    exec_participants = User.objects.none()
    for each in lecture.tasks.all():
        sv_participants |= each.supervisor.all()
        exec_participants |= each.task_executor.all()

    sv_participants = sv_participants.distinct()
    exec_participants = exec_participants.distinct()

    context = {'lecture': lecture,'sv_participants':sv_participants,'exec_participants':exec_participants}
    return render(request, 'task_management/open_lecture.html', context )

def notify_lecture_schedule(request, action, id):
    lecture = Lecture.objects.get(id=id)
    sv_participants = User.objects.none()
    exec_participants = User.objects.none()

    presenter = lecture.lead_presenter
    other_presenter = lecture.other_presenter.all()

    for each in lecture.tasks.all():
        sv_participants |= each.supervisor.all()
        exec_participants |= each.task_executor.all()

    all_pariticipants = sv_participants.distinct() | exec_participants.distinct() | lecture.other_participants.all().distinct()

    lecture.notified_users = 1
    lecture.approval_level = 1
    lecture.save()

    all_pariticipants = all_pariticipants.distinct()

    #notify participants, presenters if not notified
    if(lecture.notified_users != 0):
        t = threading.Thread(target=lecture_notification,args=(all_pariticipants,presenter,other_presenter,lecture.id))
        t.start()

    msg = "Successfully Notified Participants & Presenter(s)"

    context = {'lecture': lecture,'sv_participants':sv_participants,'exec_participants':exec_participants,'msg':msg}
    return render(request, 'task_management/open_lecture.html', context )

def lecture_notification(participants,lead_presenter, presenters,lid):

    lecture = Lecture.objects.get(id=lid)

    title = lecture.lecture_name
    schedule = timezone.localtime(lecture.schedule).strftime("%Y-%m-%d %H:%M %p")
    venue = lecture.venue

    msg_body = "Discussion scheduled on {}, at {}. You're a participant. See details in PMS ".format(schedule,venue)
    mail_subject = "Discussion on {} at {}".format(title,schedule)

    for each in participants:
        mail_and_send_sms(msg_body=msg_body,user=each,subject=mail_subject)
        sleep(1)

    msg_body_presenter = "Discussion scheduled on {}, at {}. You're Lead Presenter. See details in PMS ".format(schedule,venue)
    mail_and_send_sms(msg_body_presenter,lead_presenter,subject=mail_subject)

    msg_body_presenter = "Discussion scheduled on {}, at {}. You're a Presenter. See details in PMS ".format(
        schedule, venue)

    for each in presenters:
        mail_and_send_sms(msg_body=msg_body_presenter,user=each,subject=mail_subject)
        sleep(1)


def edit_lecture(request, action, id):
    lecture = Lecture.objects.get(id=id)
    init_param = {}
    if (request.GET.get('keyword')):
        keyword = request.GET.get('keyword')
        init_param.update({'keyword': keyword})

    form = LectureScheduleForm(instance=lecture,initial=init_param)

    if(request.method == 'POST'):
        form = LectureScheduleForm(request.POST, instance=lecture, initial=init_param)
        if form.is_valid():
            lecture = form.save()
            old_tasks = lecture.tasks.all()
            new_tasks = form.cleaned_data['tasks']

            added_tasks = set(new_tasks) - set(old_tasks)
            removed_tasks = set(old_tasks) - set(new_tasks)

            for each in removed_tasks:
                lecture.tasks.remove(each)

            for each in added_tasks:
                lecture.tasks.add(each)


            #if date has changed, set notified user = 0
            if('schedule' in form.changed_data):
                lecture.notified_users = 0

            lecture.save()

            red_url = "/lecture/open/"+str(lecture.id)
            return redirect(red_url)
    context = {'form':form}
    return render(request,'task_management/lecture_edit.html',context)


def send_msg(request,id):
    lecture = Lecture.objects.get(id=id)
    target = 'all'
    if(request.GET.get('target')):
        target = request.GET.get('target')

    group_sms_url = '/group_sms?'+'lect_id='+str(id)+"&target="+target
    return redirect(group_sms_url)


def all_lecture_participants(lecture_id):
    lecture = Lecture.objects.get(id=lecture_id)

    participants = User.objects.none()

    for each in lecture.tasks.all():
        participants |= each.supervisor.all()
        participants |= each.task_executor.all()

    participants |= lecture.other_participants.all()

    participants |= lecture.other_presenter.all()
    dp = participants.distinct()

    return dp

def add_consultant(request,action,id):
    lect = Lecture.objects.get(id=id)
    form = LectureAddConsultant()
    context = {'lecture':lect,'form':form}

    if(request.method == 'POST'):
        form = LectureAddConsultant(request.POST)
        if(form.is_valid()):
            consultant = form.cleaned_data['consultant']
            if(consultant not in lect.other_participants.all()):
                lect.other_participants.add(consultant)
                lect.save()
            if(ConsultantLecture.objects.filter(consultant=consultant,lecture=lect).count()<1):
                ConsultantLecture.objects.create(consultant=consultant, lecture=lect, assigned_by=request.user)
            msg = "Successfuly added consultant to lecture"
            context.update({'msg':msg})
            th = threading.Thread(target=send_consultant_discussion_notification, args=(lect.id,consultant))
            th.start()
    return render(request,'task_management/lect_task_add_consultant.html',context)

def consultant_qa_add_comment(request,action,id):
    con_qa = ConsultantQA.objects.get(id=id)
    init_param = {'consultant_qa':con_qa}
    form = ConsultantLectureFeedbackComment(initial=init_param)
    context = {'form': form}
    if(request.method == 'POST'):
        form = ConsultantLectureFeedbackComment(request.POST, initial=init_param)
        if(form.is_valid()):
            comment  = form.save()
            comment.user = request.user
            comment.created_date = datetime.datetime.now()
            comment.save()
            message = "Comment Added Successfully"
            context.update({'message':message})
            #TODO: send notification to consultant about the comment
    return render(request,'task_management/add_comment.html', context)