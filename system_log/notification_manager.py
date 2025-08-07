import datetime

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect

from task_management.models import GroupMsgInstruction, MsgInstructionAction
from system_log.models import MailAndSMSLog
from task_management.forms import MsgInstructionActionForm
def notification_handler(request,action=None,id=None):
    if (request.user.is_anonymous):
        return redirect('/')

    if(action == 'show'):
       return show_all_notification(request,action,id)
    if(action == 'reply'):
        return reply_notification(request,action,id)
    if(action == 'my_replys'):
        return my_replys(request,action,id)
    if(action == 'direct_messages'):
        return reply_notification(request,action,id)


def show_all_notification(request, action=None, id=None):

    if(request.user.username=='pd@rooppurnpp.gov.bd'):
        page_no = 1

        if (request.GET.get('page_no')):
            page_no = int(request.GET.get('page_no'))

        dm_list = MsgInstructionAction.objects.all().order_by('-created_at')

        no_of_items = 100
        paginator = Paginator(dm_list, no_of_items)

        try:
            dm_list = paginator.page(page_no)

        except PageNotAnInteger:
            dm_list = paginator.page(page_no)

        except EmptyPage:
            dm_list = paginator.page(paginator.num_pages)

        return render(request, 'dm_list_pd.html', {'dm_list': dm_list})

    notifications = MailAndSMSLog.objects.filter(receiver=request.user).order_by('send_time')
    notification_list = []
    for each in notifications:
        if(GroupMsgInstruction.objects.filter(message_body=each.message_body).count()>0):
            notification_list.append((each,True))
        else:
            notification_list.append((each,False))
    context = {'notification_list':notification_list}
    return render(request,'notification.html',context)


def my_replys(request,action=None,id=None):

    dm_list = MsgInstructionAction.objects.filter(created_by=request.user).order_by('-created_at')

    return render(request,'dm_list.html',{'dm_list':dm_list})

    pass
def reply_notification(request,action=None,id=None):
    init = {'user':request.user}
    if(id):
        sms_text = MailAndSMSLog.objects.get(id=id).message_body
        init .update({
            'instruction':GroupMsgInstruction.objects.get(message_body=sms_text),
        })
    form = MsgInstructionActionForm(initial=init)

    context = {'form':form}
    if(request.method == 'POST'):
        form = MsgInstructionActionForm(request.POST,initial=init)
        if(form.is_valid()):
            dm = form.save()
            dm.created_by = request.user
            dm.created_at = datetime.datetime.now()
            dm.save()
            context.update({'success':True})
    return render(request,'dm_to_pd.html',context)
