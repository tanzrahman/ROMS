from unicodedata import category

from task_management.models import *

from django import template

register = template.Library()


@register.filter(name='requires_executor_feedback')
def requires_executor_feedback(task, user):
    if (Task.objects.get(id=task).task_category == 'DocumentReview'):
        return 2
    if (ExecutorFeedBack.objects.filter(task__id=task, executor=user).count() > 0):
        return 0
    else:
        return 1

@register.filter(name='requires_ongoing_executor_feedback')
def requires_ongoing_executor_feedback(task, user):
    if((ExecutorFeedBack.objects.filter(task__id=task, executor=user).count() < 1)):
        return 0
    if(OngoingExecutorFeedBack.objects.filter(task__id=task, executor=user,approval_level__gte=1).count() > 0):
        return 0
    else:
        return 1
@register.filter(name='get_feedback')
def get_feedback(task,user):
    fb = TaskFeedBack.objects.filter(task__id=task, executor_feedback__executor=user).first()
    return fb.id

@register.filter(name='executor_task_count')
def executor_task_count(uid):

    return Task.objects.filter(task_executor__id=uid).count()

@register.filter(name='feedback_percentage')
def feedback_percentage(tasks,fb):
    if(tasks == 0):
        return 0
    if(not fb):
        fb = 0
    p = round(100*fb/tasks,2)
    return p

@register.filter(name='get_executor_feedback')
def get_executor_feedback(task,div):
    return task.executor_feedback(div)

@register.filter(name='get_executor_document_review')
def get_executor_document_review(task,user):
    doc_rev = None
    category = None
    if(OperationalDocumentReview.objects.filter(task=task,task__division=user.profile.division).count() > 0):
        doc_rev = OperationalDocumentReview.objects.filter(task=task,task__division=user.profile.division).last()
        category = 'Operational'
    if(FireAndEmergencyDocumentReview.objects.filter(task=task,task__division=user.profile.division).count() > 0):
        doc_rev = FireAndEmergencyDocumentReview.objects.filter(task=task,task__division=user.profile.division).last()
        category = 'Fire'
    if(RegulationDocumentReview.objects.filter(task=task,task__division=user.profile.division).count() > 0):
        doc_rev = RegulationDocumentReview.objects.filter(task=task,task__division=user.profile.division).last()
        category = 'Regulation'
    if(OthersDocumentReview.objects.filter(task=task,task__division=user.profile.division).count() > 0):
        doc_rev = OthersDocumentReview.objects.filter(task=task,task__division=user.profile.division).last()
        category = 'Other'
    return (doc_rev,category)