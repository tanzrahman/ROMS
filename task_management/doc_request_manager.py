import datetime
import threading
from functools import reduce
import operator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

from task_management.models import Task, User, DocumentRequest
from task_management.forms import DocumentReqeustForm, DocumentReqeustApprovalForm, DocumentProvideForm, DeliveredDocumentSearchForm, PendingDocumentSearchForm
from system_log.sms_mail_sender import send_email_only, send_email_with_cc
from manpower.models import Division
def document_request_handler(request, action='', task_id=None, doc_request_id=None):
    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')

    if (action == 'create_request'):
        return create_reqeust(request, task_id, doc_request_id)
    if (action == 'view_my_requests'):
        return view_my_requests(request)
    if (action == 'pending_requests'):
        return view_pending_requests(request)
    if(action == 'approve_request'):
        return approve_doc_request(request, task_id, doc_request_id)
    if (action == 'all_requests'):
        return all_doc_request(request, task_id, doc_request_id)
    if(action == 'provide_document'):
        return provide_doc_request(request, task_id, doc_request_id)
    if(action == 'delivered_documents'):
        return delivered_documents(request)
    if(action == 'not_received_documents'):
        return not_received_documents(request)
    if(action == 'update_remarks'):
        return update_doc_delivered_remarks(request, task_id, doc_request_id)
    if (action == 'consultant_requests'):
        return view_consultant_requests(request)
    if (action == 'approved_consultant_requests'):
        return approved_consultant_doc_requests(request)
    if (action == 'delivered_consultant_requests'):
        return delivered_consultant_doc_requests(request)
    return HttpResponse("ACTION NOT ALLOWED")


def create_reqeust(request, task_id=None, doc_request_id=None):
    task = Task.objects.get(id=task_id)
    form = DocumentReqeustForm(initial={'task_id': task_id})
    curr_day = datetime.date.today()
    todays_req = DocumentRequest.objects.filter(requested_by=request.user,requested_at__gte=curr_day)
    if(todays_req.count() >= 10):
        return HttpResponse("You Cannot Request more than 10 documents a day")

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
        context.update({'form': form})

    return render(request, 'task_management/document_request.html', context)


def view_my_requests(request, task_id=None, doc_request_id=None):
    my_requests = DocumentRequest.objects.filter(requested_by=request.user).order_by('-requested_at')
    return render(request, 'task_management/my_document_requests.html', {'my_requests': my_requests})


def delivered_documents(request):
    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    form = DeliveredDocumentSearchForm()

    filter_list = []
    if (request.GET):
        form = DeliveredDocumentSearchForm(request.GET)

        if (form.is_valid()):
            for each in form.changed_data:
                if (each == 'requested_by'):
                    filter_list.append(Q(**{each: form.cleaned_data[each]}))
                if (each == 'approved_by'):
                    filter_list.append(Q(**{each: form.cleaned_data[each]}))
                if (each == 'provided_by'):
                    filter_list.append(Q(**{each: form.cleaned_data[each]}))
                if ('start_date' in each):
                    date_filter = 'provided_at' + "__gte"
                    filter_list.append(Q(**{date_filter: form.cleaned_data[each]}))
                if ('end_date' in each):
                    date_filter = 'provided_at' + "__lte"
                    filter_list.append(Q(**{date_filter: form.cleaned_data[each]}))

    if (len(filter_list) > 0):
        delivered_doc = DocumentRequest.objects.filter(reduce(operator.and_, filter_list)).filter(approval_level=3).order_by('-requested_at')
        delivered_doc_num = DocumentRequest.objects.filter(reduce(operator.and_, filter_list)).filter(
            approval_level=3).count()

    else:
        delivered_doc = DocumentRequest.objects.filter(approval_level=3).order_by('-requested_at')
        delivered_doc_num = DocumentRequest.objects.filter(approval_level=3).count()

    no_of_items = 100
    paginator = Paginator(delivered_doc, no_of_items)

    try:
        delivered_doc = paginator.page(page_no)

    except PageNotAnInteger:
        delivered_doc = paginator.page(page_no)

    except EmptyPage:
        delivered_doc = paginator.page(paginator.num_pages)

    context = {
        'delivered_doc': delivered_doc,
        'delivered_doc_num': delivered_doc_num,
        'form': form,
    }

    return render(request, 'task_management/delivered_documents.html', context)

def not_received_documents(request):
    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    not_received_doc = DocumentRequest.objects.filter(approval_level=-1).order_by('-requested_at')
    not_received_doc_num = DocumentRequest.objects.filter(approval_level=-1).count()

    no_of_items = 100
    paginator = Paginator(not_received_doc, no_of_items)

    try:
        not_received_doc = paginator.page(page_no)

    except PageNotAnInteger:
        not_received_doc = paginator.page(page_no)

    except EmptyPage:
        not_received_doc = paginator.page(paginator.num_pages)

    context = {
        'not_received_doc': not_received_doc,
        'not_received_doc_num': not_received_doc_num,
    }

    return render(request, 'task_management/not_received_documents.html', context)


def update_doc_delivered_remarks(request, task_id, doc_request_id):
    task = Task.objects.get(id=task_id)
    doc_req = DocumentRequest.objects.get(id=doc_request_id)
    context = {'doc_req': doc_req, 'task': task}

    form = DocumentProvideForm(initial={'doc_req': doc_req, 'provided_documents': doc_req.requested_documents,
                                        'provided_at': datetime.datetime.now(),
                                        'provider_remarks': doc_req.provider_remarks})

    if (request.method == 'GET'):
        context.update({'form': form})

    if (request.method == 'POST'):
        form = DocumentProvideForm(request.POST, instance=doc_req)

        if (form.is_valid()):
            doc_req = form.save()
            doc_req.approval_level = 3
            doc_req.provided_by = request.user
            doc_req.save()
            context.update({'success': 'Successfully Provided'})
            context.update({'form': None})
        else:
            context.update({'form': form})
    return render(request, 'task_management/update_doc_delivered_remarks.html', context)


def approve_doc_request(request, task_id, doc_request_id):

    task = Task.objects.get(id=task_id)
    doc_req = DocumentRequest.objects.get(id=doc_request_id)

    context = {'doc_req': doc_req, 'task': task}

    form = DocumentReqeustApprovalForm()

    if(request.method == 'POST'):
        form = DocumentReqeustApprovalForm(request.POST,instance=doc_req)
        if(form.is_valid()):
            doc_req = form.save()
            doc_req.approval_level = 2
            doc_req.approved_at = datetime.datetime.now()
            doc_req.approved_by = request.user
            doc_req.save()
            # NOTE: send mail to documentation team
            mailer = threading.Thread(target=send_mail_for_doc_request, args=(doc_req,))
            mailer.start()
            context.update({'success': 'Successfully Approved'})
            form = ''
    context.update({'form':form})


    return render(request,'task_management/document_request_approval.html',context)


def view_pending_requests(request):

    doc_req = []

    search_form = PendingDocumentSearchForm()

    filter_list = []

    if (request.GET):
        search_form = PendingDocumentSearchForm(request.GET)

        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('task_id' in each):
                    filter_list.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                if (each == 'requested_by'):
                    filter_list.append(Q(**{each: search_form.cleaned_data[each]}))

    if (len(filter_list) > 0):
        doc_req = DocumentRequest.objects.filter(reduce(operator.and_, filter_list)).filter(
            approval_level=1).order_by('-requested_at')

    else:
        if (request.user.profile.access_level < 2):
            time_limit = datetime.datetime.now() - datetime.timedelta(days=3)
            doc_req = DocumentRequest.objects.filter(requested_at__lt=time_limit, approval_level=1).order_by(
                '-requested_at')

        elif (request.user.profile.access_level == 2):
            # list for dep cheif or dpds
            doc_req = DocumentRequest.objects.filter(approval_level=1).order_by('-requested_at')

        elif (request.user.profile.access_level == 3 or request.user.profile.access_level == 4):
            # list for div head, shop man, dep shop man, distributors
            doc_req = DocumentRequest.objects.filter(approval_level=1,
                                                     task__division=request.user.profile.division).order_by(
                '-requested_at')

        elif (request.user.profile.access_level > 4 and request.user.profile.is_supervisor == True):
            # list for div head, shop man, dep shop man, distributors
            doc_req = DocumentRequest.objects.filter(approval_level=1, task__supervisor=request.user).order_by(
                '-requested_at')

    context = {'my_requests': doc_req, 'form': search_form}

    if(request.user.profile.access_level < 2):
        list_doc_level_1 = DocumentRequest.objects.filter(approval_level=1).order_by('-requested_at')[:200]
        list_doc_level_2 = DocumentRequest.objects.filter(approval_level=2).order_by('-requested_at')[:200]
        list_doc_level_3 = DocumentRequest.objects.filter(approval_level=3).order_by('-requested_at')[:200]

        doc_level_1 = DocumentRequest.objects.filter(approval_level=1).count()
        doc_level_2 = DocumentRequest.objects.filter(approval_level=2).count()
        doc_level_3 = DocumentRequest.objects.filter(approval_level=3).count()

        doc_div_level_1 = DocumentRequest.objects.filter(approval_level=1).values('task__division__division_name').annotate(Count('id')).order_by()
        doc_div_level_2 = DocumentRequest.objects.filter(approval_level=2).values('task__division__division_name').annotate(
            Count('id')).order_by()
        doc_div_level_3 = DocumentRequest.objects.filter(approval_level=3).values('task__division__division_name').annotate(
            Count('id')).order_by()

        context.update({
                    'list_doc_level_1': list_doc_level_1,
                    #'list_doc_level_2': list_doc_level_2,
                    'list_doc_level_3': list_doc_level_3,
                    'doc_level_1': doc_level_1,
                    'doc_level_2': doc_level_2,
                    'doc_level_3': doc_level_3,
                    'doc_div_level_1': doc_div_level_1,
                    'doc_div_level_2': doc_div_level_2,
                    'doc_div_level_3': doc_div_level_3,
                  })

    return render(request, 'task_management/pending_document_requests.html', context)


def all_doc_request(request, task_id=None, doc_request_id=None):
    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    # doc_req_na = DocumentRequest.objects.filter(approval_level=-1).order_by('-requested_at')
    doc_req_new = DocumentRequest.objects.filter(approval_level=2).order_by('-requested_at')

    doc_req = doc_req_new

    no_of_items = 2000
    paginator = Paginator(doc_req, no_of_items)

    try:
        doc_req = paginator.page(page_no)

    except PageNotAnInteger:
        doc_req = paginator.page(page_no)

    except EmptyPage:
        doc_req = paginator.page(paginator.num_pages)
    return render(request, 'task_management/approved_document_requests.html', {'my_requests': doc_req})


def provide_doc_request(request, task_id=None, doc_request_id=None):
    task = Task.objects.get(id=task_id)
    doc_req = DocumentRequest.objects.get(id=doc_request_id)
    context = {'doc_req': doc_req, 'task': task}

    form = DocumentProvideForm(initial={'doc_req':doc_req, 'provided_documents':doc_req.requested_documents, 'provided_at':datetime.datetime.now()})
    if(request.method == 'GET'):
        context.update({'form': form})

    if(request.method == 'POST'):
        form = DocumentProvideForm(request.POST,instance=doc_req)

        if(form.is_valid()):
            doc_req = form.save()
            doc_req.approval_level = 3
            if (form.cleaned_data['document_not_received'] == 'no'):
                doc_req.provided_documents = ""
                doc_req.approval_level = -1
                doc_req.save()
            else:
                doc_req.provided_by = request.user
                doc_req.save()
            context.update({'success': 'Successfully Provided'})
            context.update({'form':None})
        else:
            context.update({'form':form})
    return render(request, 'task_management/document_request_approval.html', context)

def send_mail_for_doc_request(doc_req):
    # TODO: implement email sending to Documentation division for document
    msg_body = ("Document reqeust received from user: {} for documents {}, Remarks: {}. Please provide the documents to the mentioned email. -ROMS").format(doc_req.requested_by,doc_req.requested_documents,doc_req.requester_remarks)
    subject = "Document Request"

    if(doc_req.requested_by.profile.division.division_name == 'Consultancy'):
        msg_body = (
            "Document reqeust received from Consultant: {} for documents {}. Remarks: {}. \n\nPlease provide the documents in Printed Format. -ROMS").format(
            doc_req.requested_by, doc_req.requested_documents, doc_req.requester_remarks)
        subject = "Printed Document Request from Consultant"

    email_cc = list(doc_req.task.supervisor.all().values_list('email', flat=True))
    if (not doc_req.requested_by.profile.division.division_name == 'Consultancy'):
        email_cc.append(doc_req.requested_by.email)

    doc_team_email = 'documentation.site@rooppurnpp.gov.bd'
    send_email_with_cc(msg_body,subject=subject, receiver_email=doc_team_email,CC=email_cc)

def view_consultant_requests(request):

    div = Division.objects.get(division_name='Consultancy')
    doc_req = DocumentRequest.objects.filter(approval_level=1, requested_by__profile__division=div).order_by('-requested_at')

    context = {'consultant_requests': doc_req}


    return render(request, 'task_management/consultant_document_requests.html', context)


def approved_consultant_doc_requests(request):

    div = Division.objects.get(division_name='Consultancy')
    approved_doc_req = DocumentRequest.objects.filter(approval_level=2, requested_by__profile__division=div).order_by('-approved_at')

    context = {'approved_consultant_requests': approved_doc_req}


    return render(request, 'task_management/approved_consultant_document_requests.html', context)


def delivered_consultant_doc_requests(request):

    div = Division.objects.get(division_name='Consultancy')
    delivered_doc_req = DocumentRequest.objects.filter(approval_level=3, requested_by__profile__division=div).order_by('-approved_at')

    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100
    paginator = Paginator(delivered_doc_req, no_of_items)

    try:
        delivered_doc_req = paginator.page(page_no)

    except PageNotAnInteger:
        delivered_doc_req = paginator.page(page_no)

    except EmptyPage:
        delivered_doc_req = paginator.page(paginator.num_pages)

    context = {'delivered_consultant_requests': delivered_doc_req}


    return render(request, 'task_management/delivered_consultant_document_requests.html', context)