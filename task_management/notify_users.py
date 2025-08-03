import threading
import datetime
from time import sleep
from django.utils import timezone
from task_management.models import Task,Milestone, Lecture, DocumentRequest
from manpower.models import Profile, User
from system_log.sms_mail_sender import mail_and_send_sms, send_email_only


def send_task_list_notification(task_list):
    for task_id in task_list:
        task = Task.objects.get(id=task_id)
        task.status = 'A'
        task.save()
        send_notification(task_id)

def send_notification(task_id):
    #update milestone list and send notification
    print("Notify Task",task_id)
    task = Task.objects.get(id=task_id)
    if(task.milestone_id != ""):
        milestone = Milestone.objects.filter(milestone_id=task.milestone_id)
        if(milestone.count()!=0):
            for each in milestone:
                each.is_assigned = True
                each.division = task.division
                each.save()

    supervisors = task.supervisor.all()
    executors = task.task_executor.all()
    sleep(1)
    taskID = task.milestone_id
    if(task.milestone_id == ""):
        taskID = task.task_id

    msg_body = "You are assigned to {} as Supervisor. Feedback must by login ROMS in 3 days. Activity is under surveillance. -ROMS, NPCBL".format(taskID)
    for supervisor in supervisors:
        print("sending msg to supervisor, ",supervisor.first_name)
        notify = threading.Thread(target=mail_and_send_sms,args=(msg_body,supervisor))
        notify.start()
        sleep(1)

    msg_body = "You are assigned to {} as Executor. Feedback must by login ROMS in 3 days. Activity is under surveillance. -ROMS, NPCBL".format(taskID)
    for executor in executors:
        print("sending msg to executor, ",executor.first_name)
        notify = threading.Thread(target=mail_and_send_sms, args=(msg_body, executor))
        notify.start()
        sleep(1)


def send_notification_non_departmental(task_id):
    #update milestone list and send notification
    print(task_id)
    task = Task.objects.get(id=task_id)
    supervisors = task.supervisor.all()
    executors = task.task_executor.all()
    sleep(1)
    taskID = task.milestone_id
    if(task.milestone_id == ""):
        taskID = task.task_id

    msg_body = "You are assigned to a new Task as supervisor. Task ID: {}\n\n Rooppur Operational Management System".format(taskID)
    for supervisor in supervisors:
        if(supervisor.profile.division!=task.division):
            notify = threading.Thread(target=mail_and_send_sms,args=(msg_body,supervisor))
            notify.start()
        sleep(1)

    msg_body = "You are assigned to a new Task as Executor. Task ID: {}\n\n Rooppur Operational Management System".format(taskID)
    for executor in executors:
        if (executor.profile.division != task.division):
            notify = threading.Thread(target=mail_and_send_sms, args=(msg_body, executor))
            notify.start()
        sleep(1)

def send_reassign_notification(task_id,removed_sup,new_sup,removed_exc,new_added_exc):

    #TODO: implement reassignment notification
    task = Task.objects.get(id=task_id)
    taskID = task.milestone_id
    if(task.milestone_id == ""):
        taskID = task.task_id

    user_type = 'Supervisor'
    assigned_msg_body = "You are assigned to a new Task as {}. Task ID: {}\n\n Rooppur Operational Management System".format(user_type,taskID)
    removed_msg_body = "You have been removed from a Task {}. Task ID: {}\n\n Rooppur Operational Management System".format(user_type,taskID)

    for each in removed_sup:
        notify = threading.Thread(target=mail_and_send_sms, args=(removed_msg_body,each))
        notify.start()
    sleep(1)

    for each in new_sup:
        notify = threading.Thread(target=mail_and_send_sms, args=(assigned_msg_body,each))
        notify.start()
    sleep(1)

    user_type = 'Executor'
    assigned_msg_body = "You are assigned to a new Task as {}. Task ID: {}\n\n Rooppur Operational Management System".format(
        user_type, taskID)
    removed_msg_body = "You have been removed from a Task {}. Task ID: {}\n\n Rooppur Operational Management System".format(user_type,
                                                                                                              taskID)
    for each in removed_exc:
        notify = threading.Thread(target=mail_and_send_sms, args=(removed_msg_body,each))
        notify.start()
    sleep(1)

    for each in new_added_exc:
        notify = threading.Thread(target=mail_and_send_sms, args=(assigned_msg_body,each))
        notify.start()


def send_consultant_task_notification(task_id,consultant):
    #update milestone list and send notification
    print("Notify Consultant Task",task_id)
    task = Task.objects.get(id=task_id)

    taskID = task.milestone_id
    if(task.milestone_id == ""):
        taskID = task.task_id

    msg_body = "You are attached to Milestone: {} to provide Consultancy. -ROMS, NPCBL".format(taskID)
    print("sending msg to consultant, ",consultant.first_name)
    notify = threading.Thread(target=mail_and_send_sms,args=(msg_body,consultant))
    notify.start()
    sleep(1)

def send_consultant_discussion_notification(discussion_id,consultant):
    #update milestone list and send notification
    discussion = Lecture.objects.get(id=discussion_id)
    print("Notify Consultant discussion: {}, to {}".format(discussion.lecture_name, consultant.first_name))

    schedule = timezone.localtime(discussion.schedule).strftime("%Y-%m-%d %H:%M %p")
    msg_body = "You are attached to a discussion: {} on {}, to provide Consultancy. -ROMS, NPCBL".format(discussion.lecture_name,schedule)
    notify = threading.Thread(target=mail_and_send_sms,args=(msg_body,consultant))
    notify.start()
    sleep(1)

def send_consultant_docreq_notification(docreq):
    docreq = DocumentRequest.objects.get(id=docreq.id)

    msg_body = "Document Request for task : {}, From Consultant: {}".format(docreq.task,docreq.requested_by)
    pd = User.objects.get(username='md@npcbl.gov.bd')
    notify = threading.Thread(target=mail_and_send_sms,args=(msg_body,pd))
    notify.start()
    sleep(1)

def task_comment_notification(task,comment_by):
    task = Task.objects.get(id=task.id)
    supervisors = list(task.supervisor.all())
    executors = list(task.task_executor.all())
    divisional_persons = list(User.objects.filter(profile__division=task.division,profile__access_level=3))
    pd = list(User.objects.filter(username='md@npcbl.gov.bd'))
    chief = list(User.objects.filter(username__icontains='hasmat.ali'))
    receivers = supervisors + executors + divisional_persons + pd + chief

    msg = "{} commented on Task: {}, Check on ROMS, NPCBL".format(comment_by.username, task)
    subject = "Comment on Task: {}".format(task)
    for user in receivers:
        notify = threading.Thread(target=send_email_only,args=(msg,subject,user.email))
        notify.start()
        sleep(1)

def task_start_notification(task):
    pass
