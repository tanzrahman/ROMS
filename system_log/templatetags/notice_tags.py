from task_management.models import *
import datetime
from system_log.models import NoticeBoard
from django import template

register = template.Library()

@register.filter(name='get_notice')
def get_notice(curr_time):
    notice = NoticeBoard.objects.filter(expire_time__gte=datetime.datetime.now())
    if(notice.count()>0):
        return notice[0]
    return None