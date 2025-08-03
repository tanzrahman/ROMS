import threading
from time import sleep

from django.http import HttpResponse
from django.shortcuts import render
from manpower.models import Profile, User
from system_log.forms import GroupSMSForm
from django.db.models import Q
from functools import reduce
import operator
from system_log.sms_mail_sender import mail_and_send_sms
from task_management.models import Task, GroupMsgInstruction, MsgInstructionAction, Lecture
from task_management.lecture_manager import all_lecture_participants
import datetime

def handle_sms_request(request):
    if(request.user.is_staff):
        group_msgs = GroupMsgInstruction.objects.all().order_by('-send_time')
        context = {}
        context.update({'group_msg':group_msgs})
        if (request.method == 'GET'):
            form_initial = {}
            sms_form = GroupSMSForm(request.GET)
            if(request.GET.get('lect_id')):
                lect_id =request.GET.get('lect_id')
                target = request.GET.get('target')
                participants = []
                if(target == 'all'):
                    participants = all_lecture_participants(lect_id)
                    form_initial= {'user': participants}
                lecture = Lecture.objects.get(id=lect_id)
                form_initial.update({'msg_body': lecture.lecture_name})
                sms_form = GroupSMSForm(form_initial)

            context.update({
                'sms_form': sms_form
            })
            return render(request, 'group_sms.html', context)
        elif(request.method == 'POST'):
            sms_form = GroupSMSForm(request.POST)

            try:
                if(sms_form.is_valid()):
                    tasks = sms_form.cleaned_data['tasks']
                    divisions = sms_form.cleaned_data['receiver_division']
                    user_levels = sms_form.cleaned_data['receiver_designation']
                    shops = sms_form.cleaned_data['department']
                    msg_body = sms_form.cleaned_data['msg_body']
                    specific_users = sms_form.cleaned_data['user']


                    users = User.objects.filter(profile__division__in=divisions)
                    task_divisions = []

                    for each in tasks:
                        if(each not in task_divisions):
                            task_divisions.append(each.division)

                    if(len(users)==0):
                        users = User.objects.filter(profile__division__in=task_divisions)

                    if(len(shops)>0):
                        users = users.filter(profile__department__in=shops)

                    user_filters = []
                    receivers = []

                    if (len(divisions) == 1):
                        if (divisions[0].division_name == ""):
                            users = Profile.objects.all()

                    for level in user_levels:
                        if(level == 'div_head'):
                            user_filters.append(Q(**{'profile__access_level': 3}))
                        if(level == 'shop_man'):
                            user_filters.append(Q(**{'profile__designation': 'Shop Manager'}))
                        if (level == 'dep_shop_man'):
                            user_filters.append(Q(**{'profile__designation': 'Deputy Shop Manager'}))
                        if (level == 'job_dist'):
                            user_filters.append(Q(**{'profile__access_level': 4}))
                        if (level == 'supervisor'):
                            if (len(tasks) > 0):
                                for each in tasks:
                                    for sup in each.supervisor.all():
                                        if (sup not in receivers):
                                            receivers.append(sup)
                            else:
                                user_filters.append(Q(**{'profile__is_supervisor': True}))

                        if (level == 'executor'):
                            if (len(tasks) > 0):
                                for each in tasks:
                                    for exec in each.task_executor.all():
                                        if(exec not in receivers):
                                            receivers.append(exec)
                            else:
                                user_filters.append(Q(**{'profile__is_executor': True}))

                        print(level)
                    if(len(user_filters)>0):
                        users = users.filter(reduce(operator.or_, user_filters))

                    if(len(specific_users)>0):
                        if(len(users)>0):
                            users |= specific_users
                        else:
                            users = specific_users

                    for each in users:
                        receivers.append(each)

                    notify = threading.Thread(target=send_group_sms, args=(receivers, msg_body))
                    notify.start()

                    sms_form = GroupSMSForm()
                    context.update({
                        'sms_form': sms_form, 'success': 'success'
                    })
                    return render(request, 'group_sms.html', context)
                else:
                    context.update({
                        'sms_form': sms_form, 'failed': 'Error on Data Provided'
                    })
                    return render(request, 'group_sms.html', context)
            except Exception as e:
                print("GROUP_SMS_ERROR: "+e.__str__())
                context.update({
                    {'sms_form': sms_form, 'failed': 'Failed To Send SMS'}
                })
                return render(request, 'group_sms.html', context)

        else:
            return HttpResponse("You're not allowed to use this service")
    else:
        return HttpResponse("You're not allowed to use this service")


def send_group_sms(person_list,msg_body):

    recipients = ""
    for each in person_list:
        recipients = recipients + str(each.username) + ", "

    curr_time = datetime.datetime.now()
    GroupMsgInstruction.objects.create(recipients=recipients, message_body=msg_body,send_time=curr_time)
    print('person_list: ', recipients)
    for person in person_list:
        notify = threading.Thread(target=mail_and_send_sms, args=(msg_body, person))
        notify.start()
    sleep(2)