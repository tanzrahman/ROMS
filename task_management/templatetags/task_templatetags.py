from task_management.models import *
import datetime
from system_log.models import TaskLog
from django import template

register = template.Library()

@register.filter(name='task_change_log')
def task_change_log(task):
    try:
        task_logs = TaskLog.objects.filter(task=task).order_by('-created_at')
        if(task_logs.count()>0):
            return task_logs
        else:
            return None
    except Exception as e:
        print(e)
        return None