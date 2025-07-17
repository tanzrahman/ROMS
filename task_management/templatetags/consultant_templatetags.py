import datetime

from task_management.models import *

from django import template

register = template.Library()


@register.filter(name='is_discussion_participant')
def is_discussion_participant(lect_id, user):
    if (Lecture.objects.filter(id=lect_id, other_participants=user).count() > 0):
        return True
    else:
        return False

@register.filter(name='is_expired')
def is_expired(schedule):
    try:
        sched_time = schedule.timestamp()
        curr_time = datetime.datetime.now().timestamp()
        if(curr_time > sched_time):
            return True
        else:
            return False
    except Exception as e:
        print(e.__str__())
        return False

@register.filter(name='feedback_required')
def feedback_required(lecture,consultant):

    if(ConsultantLecture.objects.filter(consultant=consultant,lecture=lecture).count()>0):
        if(ConsultantQA.objects.filter(lecture=lecture,consultant=consultant).count()>0):
            return 0
        else:
            if(lecture.schedule.timestamp() > datetime.datetime.now().timestamp()):
                return 0
            return 1
    else:
        return -1

@register.filter(name='has_feedback')
def feedback_required(lecture,consultant):
    if(ConsultantQA.objects.filter(lecture=lecture,consultant=consultant).count()>0):
        return 1
    else:
        return 0

@register.filter(name='con_has_not_participated')
def con_has_not_participated(task_id,consultant):

    if(ConsultantTasks.objects.filter(task_id=task_id,consultant=consultant).count()<1):
        return True
    else:
        return False


@register.filter(name='es_feedback_available')
def es_feedback_available(task_id):
    if(TaskFeedBack.objects.filter(task_id=task_id).count()>0):
        tfb = TaskFeedBack.objects.filter(task_id=task_id).first()
        return tfb.id
    return None

@register.filter(name='task_consultant')
def task_consultant(task):
    ts = ConsultantTasks.objects.filter(task=task)
    if(ts.count()>0):
        return ts.first().consultant
    else:
        return None


@register.filter(name='can_ask_consultancy')
def can_ask_consultancy(task):
    ret = True
    if(ConsultancyRequest.objects.filter(task=task).count()>0):
        # if already made a request
        ret = False

    if(ConsultantTasks.objects.filter(task=task).count()>0):
        #already consultant added to this task
        ret = False

    return ret

@register.filter('get_consultant_feedback')
def get_consultant_feedback(lecture, consultant):
    fb = ConsultantQA.objects.filter(lecture=lecture, consultant=consultant)
    if(fb.count()>0):
        return fb.first().id
    return None

@register.filter('get_consultant_feedback_time')
def get_consultant_feedback_time(lecture, consultant):
    fb = ConsultantQA.objects.filter(lecture=lecture, consultant=consultant)
    if (fb.count() > 0):
        return fb.first().created_at
    return None