from task_management.models import *
import datetime
from django import template

register = template.Library()

@register.filter(name='todays_comments')
def todays_comments(task):
    todays_time = datetime.date.today()
    try:
        today_comments = Comment.objects.filter(task_id=task,created_date__day=todays_time.day, created_date__month=todays_time.month, created_date__year=todays_time.year)
        today_comments = today_comments.count()
        total_comments = Comment.objects.filter(task_id=task).count()
        return (today_comments,total_comments)
    except Exception as e:
        print(e)

@register.filter(name='get_comments')
def get_comments(task):
    print(task)
    comments = Comment.objects.filter(task_id=task)
    if(comments.count()>0):
        return comments
    return None