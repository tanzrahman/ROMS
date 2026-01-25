import datetime
import os
import threading

from django.core import paginator
from django.db.models import Count
from django.dispatch import receiver

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from xhtml2pdf import pisa

from system_log.sms_mail_sender import send_email_with_cc
from task_management.forms import *
import csv
from io import StringIO, BytesIO
from task_management.notify_users import send_reassign_notification, send_consultant_task_notification, send_email_only
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from system_log.models import TaskLog
import json
from task_management.models import *
from task_management.forms_doc_review import OperationalDocumentReviewForm, RegulationDocumentReviewForm, \
    OthersDocumentReviewForm, FireAndEmergencyDocumentReviewForm, DocRevAssignCommittee, ApprovalSignatureForm, \
    SafetyAnalysisReportReviewForm, SARCommitteeReportForm, ApprovalSignatureForm_MD

from task_management.ftp_handler import FILETYPE, upload_to_ftp
from system_log.sms_mail_sender import doc_review_mail_and_send_sms
from time import sleep
from django.conf import settings


def doc_review_handler(request,action=None,id=None):
    if(request.user.is_anonymous):
        return redirect('/')
    if(action == 'list'):
        return list_all_doc(request, action, id)
    if(action == 'open'):
        return open_doc_review(request,id)
    if(action == 'feedback'):
        return document_feedback(request,id)
    if(action == 'list_review_report'):
        return show_doc_review_feedbacks(request,id)
    if(action == 'open_review'):
        return view_specific_review(request,id)
    if (action == 'assign_committee'):
        return assign_doc_rev_committee(request, id)
    if(action=='second_tier_doc_review_list'):
        return second_tier_doc_review_list(request)
    if(action=='pms_second_tier_doc_review_list'):
        return pms_second_tier_doc_review_list(request)
    if(action=='second_tier_doc_review'):
        return second_tier_doc_review(request)
    if(action=='committee_open_review'):
        return open_doc_rev_by_committee(request,id)
    if(action=='pms_committee_open_review'):
        return pms_open_doc_rev_by_committee(request,id)
    if (action == 'recommend'):
        return committee_recomendation(request, id)
    if (action == 'review_comment'):
        return committee_review_comment(request, id)
    if (action == 'edit_review_comment'):
        return edit_review_comment(request, id)
    if (action == 'download_committee_review'):
        return download_committee_review(request, id)
    if (action == 'pms_download_committee_review'):
        return pms_download_committee_review(request, id)
    if (action == 'assign_sar_reviewer'):
        return assign_sar_reviewer(request)
    if(action == 'delete_sar_reviewer'):
        return delete_sar_reviewer(request,id)
    if(action == 'my_sar_review'):
        return my_sar_review_list(request)
    if(action == 'upload_sar_individual_report'):
        return upload_sar_individual_report(request, id)
    if(action == 'view_sar_indv_report_list'):
        return view_sar_indv_report_list(request)
    if(action == 'view_sar_reviews'):
        return view_sar_indv_report_list(request,committee_lead=request.user)
    if(action=='upload_committee_report'):
        return upload_committee_report(request, id)
    if (action == 'view_sar_comt_report_list'):
        return view_sar_committee_report(request, id)
    if(action == 'change_document_recommendation'):
        return change_document_recommendation(request, id)
    if (action == 'doc_rev_st_all_approve'):
        return second_tier_all_approve(request, id)


    return render(request, 'document_review/doc_review_base.html')

def list_all_doc(request,action=None,id=None):
    as_supervisor = Task.objects.filter(task_category='DocumentReview', supervisor=request.user, created_date__gt='2025-07-31')
    as_executor = Task.objects.filter(task_category='DocumentReview', task_executor=request.user, created_date__gt='2025-07-31')
    total = as_supervisor.union(as_executor)
    context = {"doc_list": total}
    return render(request, 'document_review/assigned_docs.html', context)


def open_doc_review(request,id):
    task = Task.objects.get(id=id)
    context = {"task": task}
    comment_list = Comment.objects.filter(task_id=task)
    if(comment_list.count()>0):
        context.update({"comment_list": comment_list})
    return render(request,'document_review/open_doc_review.html',context=context)


def document_feedback(request,id):
    doc_category = request.GET.get('doc_category')
    if(doc_category == 'Operational'):
        return operation_doc_feedback(request,id)
    if (doc_category == 'Regulation'):
        return regulation_doc_feedback(request, id)
    if (doc_category == 'Other'):
        return other_doc_feedback(request, id)
    if(doc_category == 'Fire'):
        return fire_safety_doc_feedback(request, id)
    context = {}
    return render(request,'document_review/doc_feedback.html',context=context)


def regulation_doc_feedback(request,id):
    task = Task.objects.get(id=id)
    form = RegulationDocumentReviewForm(initial={'task': task})
    doc_review = None
    if (RegulationDocumentReview.objects.filter(task=task, user=request.user).exists()):
        doc_review = RegulationDocumentReview.objects.get(task=task, user=request.user)
        form = RegulationDocumentReviewForm(initial={'task': task}, instance=doc_review)
    context = {"form": form, 'task': task}

    if (request.method == 'POST'):
        form = RegulationDocumentReviewForm(request.POST, initial={'task': task})
        if (doc_review != None):
            form = RegulationDocumentReviewForm(request.POST, initial={'task': task}, instance=doc_review)
        if (form.is_valid()):
            odr = form.save(commit=True)
            odr.user = request.user
            if (request.POST.get("final_submission") == '1'):
                odr.approval_level =2
                context.update({'final_submission': True})
            odr.save()
            context.update({'saved': 'saved'})
            context.update({"form": form})
        else:
            context.update({"form": form})
    return render(request, 'document_review/doc_feedback.html', context=context)


def operation_doc_feedback(request,id):
    task = Task.objects.get(id=id)
    form = OperationalDocumentReviewForm(initial={'task': task})
    doc_review = None
    if (OperationalDocumentReview.objects.filter(task=task, user=request.user).exists()):
        doc_review = OperationalDocumentReview.objects.get(task=task, user=request.user)
        form = OperationalDocumentReviewForm(initial={'task': task}, instance=doc_review)
    context = {"form": form, 'task': task}

    if(request.method == 'POST'):
        form = OperationalDocumentReviewForm(request.POST, initial={'task': task})
        if(doc_review != None):
            form = OperationalDocumentReviewForm(request.POST, initial={'task': task}, instance=doc_review)
        if(form.is_valid()):
            odr = form.save(commit=True)
            odr.user = request.user
            if (request.POST.get("final_submission") == '1'):
                odr.approval_level =2
                context.update({'final_submission': True})
            odr.save()
            context.update({'saved': 'saved'})
            context.update({"form": form})
        else:
            context.update({"form": form})
    return render(request, 'document_review/doc_feedback.html', context=context)



def other_doc_feedback(request,id):
    task = Task.objects.get(id=id)
    form = OthersDocumentReviewForm(initial={'task': task})
    doc_review = None
    if (OthersDocumentReview.objects.filter(task=task, user=request.user).exists()):
        doc_review = OthersDocumentReview.objects.get(task=task, user=request.user)
        form = OthersDocumentReviewForm(initial={'task': task}, instance=doc_review)
    context = {"form": form, 'task': task}

    if(request.method == 'POST'):
        form = OthersDocumentReviewForm(request.POST, initial={'task': task})
        if(doc_review != None):
            form = OthersDocumentReviewForm(request.POST, initial={'task': task}, instance=doc_review)
        if(form.is_valid()):
            odr = form.save(commit=True)
            odr.user = request.user
            if (request.POST.get("final_submission") == '1'):
                odr.approval_level = 2
                context.update({'final_submission': True})
            odr.save()
            context.update({'saved': 'saved'})
            context.update({"form": form})
        else:
            context.update({"form": form})
    return render(request, 'document_review/doc_feedback.html', context=context)

def fire_safety_doc_feedback(request,id):
    task = Task.objects.get(id=id)
    form = FireAndEmergencyDocumentReviewForm(initial={'task': task})
    doc_review = None
    if (FireAndEmergencyDocumentReview.objects.filter(task=task, user=request.user).exists()):
        doc_review = FireAndEmergencyDocumentReview.objects.get(task=task, user=request.user)
        form = FireAndEmergencyDocumentReviewForm(initial={'task': task}, instance=doc_review)
    context = {"form": form, 'task': task}

    if(request.method == 'POST'):
        form = FireAndEmergencyDocumentReviewForm(request.POST, initial={'task': task})
        if(doc_review != None):
            form = FireAndEmergencyDocumentReviewForm(request.POST, initial={'task': task}, instance=doc_review)
        if(form.is_valid()):
            odr = form.save(commit=True)
            odr.user = request.user
            if (request.POST.get("final_submission") == '1'):
                odr.approval_level = 2
                context.update({'final_submission': True})
            odr.save()
            context.update({'saved': 'saved'})
            context.update({"form": form})
        else:
            context.update({"form": form})
    return render(request, 'document_review/doc_feedback.html', context=context)

def show_doc_review_feedbacks(request,id):

    page_no = 1
    no_of_items = 200

    search_form = DocumentReviewSearchForm()

    filter_list = []

    if (request.GET):
        search_form = DocumentReviewSearchForm(request.GET)

        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('task_id' in each):
                    filter_list.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                if ('title' in each):
                    filter_list.append(Q(**{'task__title__icontains': search_form.cleaned_data[each].upper()}))
                if (each == 'division'):
                    filter_list.append(Q(**{'task__division': search_form.cleaned_data[each]}))
                if (each == 'department'):
                    filter_list.append(Q(**{'task__dept_id': search_form.cleaned_data[each]}))
                if (each == 'user'):
                    filter_list.append(Q(**{each + "__in": search_form.cleaned_data[each]}))

    if (len(filter_list) > 0):
        op_doc = OperationalDocumentReview.objects.filter(task__created_date__gt='2025-07-31').filter(reduce(operator.and_, filter_list))
        total_op_doc = len(op_doc)
        regulation_doc = RegulationDocumentReview.objects.filter(task__created_date__gt='2025-07-31').filter(reduce(operator.and_, filter_list))
        total_reg_doc = len(regulation_doc)
        fire_doc = FireAndEmergencyDocumentReview.objects.filter(task__created_date__gt='2025-07-31').filter(reduce(operator.and_, filter_list))
        total_fire_doc = len(fire_doc)
        other_doc = OthersDocumentReview.objects.filter(task__created_date__gt='2025-07-31').filter(reduce(operator.and_, filter_list))
        total_other_doc = len(other_doc)

    else:
        op_doc = OperationalDocumentReview.objects.filter(task__created_date__gt='2025-07-31')
        total_op_doc = len(op_doc)
        regulation_doc = RegulationDocumentReview.objects.filter(task__created_date__gt='2025-07-31')
        total_reg_doc = len(regulation_doc)
        fire_doc = FireAndEmergencyDocumentReview.objects.filter(task__created_date__gt='2025-07-31')
        total_fire_doc = len(fire_doc)
        other_doc = OthersDocumentReview.objects.filter(task__created_date__gt='2025-07-31')
        total_other_doc = len(other_doc)

    all_reviews = list(op_doc) + list(regulation_doc) + list(fire_doc) + list(other_doc)
    total_reviews = len(all_reviews)

    # for download list as csv
    if (request.GET.get('download')):
        if (request.GET.get('download') == 'excel'):
            print("Send CSV report")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="1st_tier_list.csv"'
            writer = csv.writer(response)
            writer.writerow(
                ["Document ID", "Title", "Final Submission", "Division", "Review By", "Feedback Date", "Last Updated"])
            for each in all_reviews:
                row = []
                row.append(each.task)
                row.append(each.task.title)
                if (each.approval_level > 1):
                    row.append("Yes")
                else:
                    row.append("No")
                row.append(each.task.division)
                row.append(each.user)
                row.append(each.created_at)
                row.append(each.modified_at)
                writer.writerow(row)
            return response

    paginator = Paginator(all_reviews, no_of_items)

    if(request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))
    try:
        all_reviews = paginator.page(page_no)

    except PageNotAnInteger:
        all_reviews = paginator.page(page_no)

    except EmptyPage:
        all_reviews = paginator.page(paginator.num_pages)

    context = {
                "all_reviews": all_reviews,
                "total_reviews": total_reviews,
                "total_op_doc": total_op_doc,
                "total_reg_doc": total_reg_doc,
                "total_fire_doc": total_fire_doc,
                "total_other_doc": total_other_doc,
                "form": search_form,
                }

    return render(request,'document_review/doc_review_feedbacks.html', context)

def view_specific_review(request,id):
    doc_id = id
    category = request.GET.get('category')
    feedback = None
    form = None
    if(category == 'Operational'):
        feedback = OperationalDocumentReview.objects.get(id=doc_id)
        form = OperationalDocumentReviewForm(instance=feedback,initial={'task': feedback.task})
    if(category == 'Regulation'):
        feedback = RegulationDocumentReview.objects.get(id=doc_id)
        form = RegulationDocumentReviewForm(instance=feedback, initial={'task': feedback.task})
    if (category == 'Fire'):
        feedback = FireAndEmergencyDocumentReview.objects.get(id=doc_id)
        form = FireAndEmergencyDocumentReviewForm(instance=feedback, initial={'task': feedback.task})
    if (category == 'Other'):
        feedback = OthersDocumentReview.objects.get(id=doc_id)
        form = OthersDocumentReviewForm(instance=feedback, initial={'task': feedback.task})
    context= {
        'form':form,
        'feedback': feedback
    }
    return render(request,'document_review/view_doc_feedback.html',context=context)


def second_tier_doc_review_list(request, action=None, id=None):
    page_no = 1
    no_of_items = 200

    search_form = SecondTierReviewSearchForm()

    filter_list = []

    if (request.GET):
        search_form = SecondTierReviewSearchForm(request.GET)

        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('task_id' in each):
                    filter_list.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                if ('title' in each):
                    filter_list.append(Q(**{'task__title__icontains': search_form.cleaned_data[each].upper()}))
                if (each == 'division'):
                    filter_list.append(Q(**{'task__division': search_form.cleaned_data[each]}))
                if (each == 'department'):
                    filter_list.append(Q(**{'task__dept_id': search_form.cleaned_data[each]}))
                if (each == 'committee'):
                    filter_list.append(Q(**{'committee': search_form.cleaned_data[each]}))
                if (each == 'div_head_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'division_head_approval__isnull': value}))
                if (each == 'chief_engr_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'chief_eng_approval__isnull': value}))
                if (each == 'sd_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'sd_approval__isnull': value}))

    if (len(filter_list) > 0):
        doc_list = SecondTierDocumentReview.objects.filter(task__created_date__gt='2025-07-31').filter(reduce(operator.and_, filter_list)).annotate(count=Count('committee_approval')).order_by('-count')
    else:
        doc_list = SecondTierDocumentReview.objects.filter(task__created_date__gt='2025-07-31').annotate(count=Count('committee_approval')).order_by('-count')

    total_reviews = len(doc_list)

    # for download list as excel
    if (request.GET.get('download')):
        if (request.GET.get('download') == 'excel'):
            print("Send CSV report")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="committee_recommendation_list.csv"'
            writer = csv.writer(response)
            writer.writerow(
                ["Task", "Title", "Division", "Department/Shop", "Committee", "Assigned Date", "Deadline",
                 "Div Head Recommendation", "CE Recommendation", "SD Recommendation"])
            for each in doc_list:
                row = []
                row.append(each.task)
                row.append(each.task.title)
                row.append(each.task.division)
                row.append(each.task.dept_id)
                row.append(each.committee)
                row.append(each.assigned_date)
                row.append(each.committee_deadline)
                if(each.division_head_approval == None):
                    row.append("")
                else:
                    row.append(each.division_head_approval.remarks)
                if(each.chief_eng_approval == None):
                    row.append("")
                else:
                    row.append(each.chief_eng_approval.remarks)
                if(each.sd_approval == None):
                    row.append("")
                else:
                    row.append(each.sd_approval.remarks)
                writer.writerow(row)
            return response


    paginator = Paginator(doc_list, no_of_items)

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))
    try:
        doc_list = paginator.page(page_no)

    except PageNotAnInteger:
        doc_list = paginator.page(page_no)

    except EmptyPage:
        doc_list = paginator.page(paginator.num_pages)

    context = {
            'doc_list': doc_list,
            'total_reviews': total_reviews,
            'form': search_form,
    }

    return render(request, 'document_review/second_tier_doc_review_list.html', context)


def pms_second_tier_doc_review_list(request, action=None, id=None):
    # to change MD sir's approval remarks
    doc_list_ = SecondTierDocumentReview.objects.filter(task__created_date__lt='2025-07-31', sd_approval__remarks__isnull=False, task__task_id__in=[ "RPR.0534.0.0.UYB.SAB26.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB30.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB31.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB42.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB43.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB44.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB45.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB81.OP.DC0001" ,
 "RPR.0534.0.0.UST.00SAT23.OP.DC0001" ,
 "RPR.0534.0.0.UST.00SAT40.OP.DC0001" ,
 "RPR.0534.0.0.UST.00SAT51.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB23.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB27.OP.DC0001" ,
 "RPR.0534.0.0.UYB.SAB80.OP.DC0001" ,
 "RPR.0534.0.0.UAC.OP.DC0004" ,
 "RPR.0534.0.0.UKU.OP.DC0003" ,
 "RPR.0534.0.0.URE.UGA.OP.DC0010" ,
 "RPR.0534.0.0.USF.OP.DC0008" ,
 "RPR.0534.0.0.UTF.OP.DC0008" ,
 "RPR.0534.0.0.UTH.OP.DC0004" ,
 "RPR.0534.0.0.UYP.OP.DC0007" ,
 "RPR.0534.0.0.USV.OP.DC0009" ,
 "RPR.0534.0.0.UYH.OP.DC0010" ,
 "RPR.0534.0.0.UYB.KLS.OP.DC0006" ,
 "RPR.0534.0.0.UYB.KLS.OP.DC0002" ,
 "RPR.0534.0.0.UYB.KLS.OP.DC0005" ,
 "RPR.0534.0.0.UYB.KLS.OP.DC0004" ,
 "RPR.0534.0.0.UYB.KLS.OP.DC0003" ,
 "RPR.0534.1.0.UKC.UKS.SMK.OP.DC0001" ,
 "RPR.0534.1.0.UMA.SMM.OP.DC0002" ,
 "RPR.0534.1.0.UJA.SMJ.OP.DC0001" ,
 "RPR.0534.1.0.UMA.SMM.OP.DC0001" ,
 "RPR.0534.1.0.UJA.FCB.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JDA.TP.DC0002" ,
 "RPR.0534.1.0.UJA.JDA.TP.DC0004" ,
 "RPR.0534.1.0.UJA.SMJ.OP.DC0002" ,
 "RPR.0534.1.0.UJA.UKC.FAL.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KUE.OP.DC0001" ,
 "RPR.0534.1.0.UMX.LDF.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KPM40.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KBH.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KPJ.OP.DC0001" ,
 "RPR.0534.1.0.UKC.LCQ50.OP.DC0001" ,
 "RPR.0534.1.0.UKC.SW.TM.DF0001" ,
 "RPR.0534.1.0.UMA.UMX.QUH.OP.DC0001" ,
 "RPR.0534.1.0.PB.TH.DC0001" ,
 "RPR.0534.1.0.UMX.LDP.OP.DC0001" ,
 "RPR.0534.1.0.UMX.LDR.OP.DC0001" ,
 "RPR.0534.1.0.UKC.OP.DC0033" ,
 "RPR.0534.1.0.UJA.OP.DC0033" ,
 "RPR.0534.1.0.SRP.OP.DC0038" ,
 "RPR.0534.1.0.OP.BE0001" ,
 "RPR.0534.1.0.OP.PF0001" ,
 "RPR.0534.1.0.OP.BE0002" ,
 "RPR.0534.1.0.OP.BE0003" ,
 "RPR.0534.1.0.AT.BE0002" ,
 "RPR.0534.1.0.UJA.TH.OP.DC0001" ,
 "RPR.0534.1.0.BB.BC.BD.EE.OP.DC0001" ,
 "RPR.0534.1.0.BF.BG.BJ.OP.DC0001" ,
 "RPR.0534.1.0.BFT.OP.DC0001" ,
 "RPR.0534.1.0.BAA.BAC.OP.DC0001" ,
 "RPR.0534.1.0.BGT.BFT.BHT.EE.OP.DC0001" ,
 "RPR.0534.1.0.BGT.OP.DC0001" ,
 "RPR.0534.1.0.CE.DC0013" ,
 "RPR.0534.1.0.UMA.MKA.OP.DC0001" ,
 "RPR.0534.1.0.BB.BC.BD.OP.DC0001" ,
 "RPR.0534.1.0.BRT.BRU.OP.DC0001" ,
 "RPR.0534.1.0.BTL.BTM.OP.DC0001" ,
 "RPR.0534.1.0.BUP.OP.DC0001" ,
 "RPR.0534.1.0.BVA.TP.DC0001" ,
 "RPR.0534.1.0.BVC.TP.DC0001" ,
 "RPR.0534.1.0.EM.EW.OP.DC0001" ,
 "RPR.0534.1.0.MKA-BAT.EE.OP.DC0001" ,
 "RPR.0534.1.0.BAY.BBY.EE.OP.DC0001" ,
 "RPR.0534.1.0.BBY.EE.OP.DC0003" ,
 "RPR.0534.1.0.ET.EM.EE.DF0111" ,
 "RPR.0534.1.0.BAT.BBT.TP.DC0001" ,
 "RPR.0534.1.0.BAT.BBT.TP.DC0002" ,
 "RPR.0534.1.0.BBT.OP.DC0001" ,
 "RPR.0534.1.0.BFL.BFM.TP.DC0001" ,
 "RPR.0534.1.0.BR.TP.DC0002" ,
 "RPR.0534.1.0.BR.TP.DC0011" ,
 "RPR.0534.1.0.BRT.TP.DC0003" ,
 "RPR.0534.1.0.BRT.TP.DC0004" ,
 "RPR.0534.1.0.BRT.TP.DC0005" ,
 "RPR.0534.1.0.BRT.TP.DC0006" ,
 "RPR.0534.1.0.BRT.TP.DC0007" ,
 "RPR.0534.1.0.BRU.TP.DC0007" ,
 "RPR.0534.1.0.BRU.TP.DC0008" ,
 "RPR.0534.1.0.BT.OP.DC0002" ,
 "RPR.0534.1.0.BY.OP.DC0005" ,
 "RPR.0534.1.0.MKA.TP.DC0004" ,
 "RPR.0534.1.0.SM.OP.DC0002" ,
 "RPR.0534.1.0.UJA.OP.DC0002" ,
 "RPR.0534.1.0.XLA.EE.OP.DC0002" ,
 "RPR.0534.1.0.XLA.OP.DC0001" ,
 "RPR.0534.1.0.BRU.TP.DC0004" ,
 "RPR.0534.1.0.BRU.TP.DC0005" ,
 "RPR.0534.1.0.BRU.TP.DC0006" ,
 "RPR.0534.1.0.BUA.TP.DC0001" ,
 "RPR.0534.1.0.BUB.TP.DC0001" ,
 "RPR.0534.1.0.BUC.TP.DC0001" ,
 "RPR.0534.1.0.BUD.TP.DC0001" ,
 "RPR.0534.1.0.BUE.TP.DC0001" ,
 "RPR.0534.1.0.BUF.TP.DC0001" ,
 "RPR.0534.1.0.BVB.TP.DC0001" ,
 "RPR.0534.1.0.BVD.TP.DC0001" ,
 "RPR.0534.1.0.BY.OP.DC0008" ,
 "RPR.0534.1.0.ET.EM.EE.DF0007" ,
 "RPR.0534.1.0.ET.EM.EE.DF0012" ,
 "RPR.0534.1.0.UJA.FCB.EM.DC0001" ,
 "RPR.0534.1.0.UMA.MKC.OP.DC0001" ,
 "RPR.0534.1.0.XKA.OP.DC0002" ,
 "RPR.0534.1.0.BFN.BFP.TP.DC0001" ,
 "RPR.0534.1.0.BUE.ET.OP.DC0001" ,
 "RPR.0534.1.0.A..B..DZ0062" ,
 "RPR.0534.1.0.A..B..DZ0063" ,
 "RPR.0534.1.0.A.B.DZ0064" ,
 "RPR.0534.1.0.BUA.TP.DC0011" ,
 "RPR.0534.1.0.BUB.TP.DC0011" ,
 "RPR.0534.1.0.BUC.TP.DC0011" ,
 "RPR.0534.1.0.BUD.TP.DC0011" ,
 "RPR.0534.1.0.BUF.TP.DC0111" ,
 "RPR.0534.1.0.BY.OP.DC0006" ,
 "RPR.0534.1.0.CF.OP.DC0002" ,
 "RPR.0534.1.0.ET.EM.EE.DF0013" ,
 "RPR.0534.1.0.ET.EM.EE.DF0014" ,
 "RPR.0534.1.0.ET.EM.EE.DF0017" ,
 "RPR.0534.1.0.MKA.TP.DC0001" ,
 "RPR.0534.1.0.MKA.TP.DC0003" ,
 "RPR.0534.1.0.XLA.EE.OP.DC0011" ,
 "RPR.0534.1.0.ET.EM.EE.DF0015" ,
 "RPR.0534.1.0.BN.PF0001" ,
 "RPR.0534.1.0.JKA.OP.DC0002" ,
 "RPR.0534.1.0.JKS.OP.DZ0001" ,
 "RPR.0534.1.0.UJA.JDA.TP.DC0001" ,
 "RPR.0534.1.0.UJA.FBA.TP.DC0002" ,
 "RPR.0534.1.0.UJA.UKU.TP.DC0011" ,
 "RPR.0534.1.0.UJA.UKU.TP.DC0012" ,
 "RPR.0534.1.0.JDA.OP.DC0001" ,
 "RPR.0534.1.0.JDK.OP.DC0001" ,
 "RPR.0534.1.0.JKA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JKA.TP.DF0001" ,
 "RPR.0534.1.0.UKC.AE.DC0001" ,
 "RPR.0534.1.0.RS.DC0001" ,
 "RPR.0534.1.0.RS.DC0002" ,
 "RPR.0534.1.0.CF.RK.OP.DC0001" ,
 "RPR.0534.1.0.CF.RK.TP.DC0001" ,
 "RPR.0534.1.0.RK.AK.OP.DC0077" ,
 "RPR.0534.1.0.RK.OP.DF0001" ,
 "RPR.0534.1.0.UKC.KPN.OP.DC0001" ,
 "RPR.0534.1.0.JMA.SCC.OP.DC0001" ,
 "RPR.0534.1.0.JMA.JNB50-80.OP.DC0001" ,
 "RPR.0534.1.0.UJA.FAK.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JNG50-80.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KRA10-20.OP.DC0001" ,
 "RPR.0534.1.0.KAA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JME.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMF.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.JNB10-40.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KBC10-30.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KBC40.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KWA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KWB50.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KBB.OP.DC0001" ,
 "RPR.0534.1.0.PE.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMK.JML.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KUA10-50.OP.DC0001" ,
 "RPR.0534.1.0.UJA.PGB50.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.FAK.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.JMN.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.JNA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KTB.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KWC.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.LCQ10-40.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KBE50-60.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JEC.OP.DC0002" ,
 "RPR.0534.1.0.UJA.JMT.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMU.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KTP.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KTQ.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KBA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KPL.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KPM.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KTA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KTC10-20.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.KTH.OP.DC0001" ,
 "RPR.0534.1.0.UJA.FAB.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JEA10-40.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JEA50-90.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JEB10-40.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JEF.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMG.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JMY20.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JND.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JNG10-40.OP.DC0001" ,
 "RPR.0534.1.0.UJA.OP.DC0011" ,
 "RPR.0534.1.0.UJA.UKC.TM.DF0001" ,
 "RPR.0534.1.0.UJA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.TP.DC0024" ,
 "RPR.0534.1.0.UJA.TP.DC0033" ,
 "RPR.0534.1.0.UJA.TP.DC0038" ,
 "RPR.0534.1.0.UJA.TP.DC0042" ,
 "RPR.0534.1.0.UJA.TP.DC0043" ,
 "RPR.0534.1.0.UJA.TP.DC0046" ,
 "RPR.0534.1.0.UJA.TP.DC0047" ,
 "RPR.0534.1.0.UJA.TP.DC0048" ,
 "RPR.0534.1.0.UJA.TP.DC0053" ,
 "RPR.0534.1.0.UJA.TP.DC0054" ,
 "RPR.0534.1.0.UJA.TP.DC0060" ,
 "RPR.0534.1.0.UJA.TP.DC0071" ,
 "RPR.0534.1.0.UJA.TP.DC0072" ,
 "RPR.0534.1.0.UJA.TP.DC0073" ,
 "RPR.0534.1.0.UJA.TP.DC0074" ,
 "RPR.0534.1.0.UJA.JE.TH.DC0001" ,
 "RPR.0534.1.0.UJA.JE.TH.DC0002" ,
 "RPR.0534.1.0.UJA.JE.TH.DC0003" ,
 "RPR.0534.1.0.UJA.PT.DC0002" ,
 "RPR.0534.1.0.UJA.QFA.OP.DC0001" ,
 "RPR.0534.1.0.UJA.TP.DC0001" ,
 "RPR.0534.1.0.UJA.TP.DC0002" ,
 "RPR.0534.1.0.UJA.TP.DC0005" ,
 "RPR.0534.1.0.UJA.TP.DC0007" ,
 "RPR.0534.1.0.UJA.TP.DC0008" ,
 "RPR.0534.1.0.UJA.TP.DC0009" ,
 "RPR.0534.1.0.UJA.TP.DC0010" ,
 "RPR.0534.1.0.UJA.TP.DC0011" ,
 "RPR.0534.1.0.UJA.TP.DC0014" ,
 "RPR.0534.1.0.UJA.TP.DC0016" ,
 "RPR.0534.1.0.UJA.TP.DC0017" ,
 "RPR.0534.1.0.UJA.TP.DC0018" ,
 "RPR.0534.1.0.UJA.TP.DC0025" ,
 "RPR.0534.1.0.UJA.TP.DC0031" ,
 "RPR.0534.1.0.UJA.TP.DC0034" ,
 "RPR.0534.1.0.UJA.TP.DC0035" ,
 "RPR.0534.1.0.UJA.TP.DC0036" ,
 "RPR.0534.1.0.UJA.TP.DC0045" ,
 "RPR.0534.1.0.UJA.TP.DC0049" ,
 "RPR.0534.1.0.UJA.TP.DC0050" ,
 "RPR.0534.1.0.UJA.TP.DC0051" ,
 "RPR.0534.1.0.UJA.TP.DC0052" ,
 "RPR.0534.1.0.UJA.TP.DC0055" ,
 "RPR.0534.1.0.UJA.TP.DC0056" ,
 "RPR.0534.1.0.UJA.TP.DC0057" ,
 "RPR.0534.1.0.UJA.TP.DC0058" ,
 "RPR.0534.1.0.UJA.TP.DC0059" ,
 "RPR.0534.1.0.UJA.TP.DC0064" ,
 "RPR.0534.1.0.UJA.TP.DC0066" ,
 "RPR.0534.1.0.UJA.TP.DC0067" ,
 "RPR.0534.1.0.UJA.TP.DC0068" ,
 "RPR.0534.1.0.UJA.TP.DC0069" ,
 "RPR.0534.1.0.UJA.TP.DC0070" ,
 "RPR.0534.1.0.UKC.PT.DC0002" ,
 "RPR.0534.1.0.XJ.OP.DC0001" ,
 "RPR.0534.1.0.TH.DZ0002" ,
 "RPR.0534.1.0.UJA.JA.OP.DC0001" ,
 "RPR.0534.1.0.AT.TH.OP.DC0003" ,
 "RPR.0534.1.0.UBN.XJA.AT.OP.DC0001" ,
 "RPR.0534.1.0.UJA.JE.TH.DC0005" ,
 "RPR.0534.1.0.UJA.JEA10-40.OP.DC0002" ,
 "RPR.0534.1.0.UJA.PT.DC0001" ,
 "RPR.0534.1.0.UJA.TP.DC0004" ,
 "RPR.0534.1.0.UJA.TP.DC0012" ,
 "RPR.0534.1.0.UJA.TP.DC0022" ,
 "RPR.0534.1.0.UJA.TP.DC0023" ,
 "RPR.0534.1.0.UJA.TP.DC0028" ,
 "RPR.0534.1.0.UJA.TP.DC0029" ,
 "RPR.0534.1.0.UJA.TP.DC0062" ,
 "RPR.0534.1.0.UJA.TP.DC0063" ,
 "RPR.0534.1.0.UKC.PT.DC0003" ,
 "RPR.0534.1.0.URE.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UKC.BN.DC0001" ,
 "RPR.0534.1.0.CE.DC0011" ,
 "RPR.0534.1.0.CE.DC0014" ,
 "RPR.0534.1.0.BN.DZ0001" ,
 "RPR.0534.1.0.TH.DC0004" ,
 "RPR.0534.1.0.UJA10.OP.PF0097" ,
 "RPR.0534.1.0.UMA10.OP.DF0200" ,
 "RPR.0534.1.0.BN.DC0003" ,
 "RPR.0534.1.0.CX.AK.OP.DC0001" ,
 "RPR.0534.1.0.UJA10.OP.DC00104" ,
 "RPR.0534.1.0.UJA10.OP.DF0033" ,
 "RPR.0534.1.0.UKC.AT.OP.DC0007" ,
 "RPR.0534.1.0.UMA.AT.OP.DF0001" ,
 "RPR.0534.1.0.UMA10.OP.DC0041" ,
 "RPR.0534.1.0.UMA10.OP.DC0142" ,
 "RPR.0534.1.0.JE.AT.OP.DC0001" ,
 "RPR.0534.1.0.UJA10.OP.DC0054" ,
 "RPR.0534.1.0.UJA10.OP.DC0057" ,
 "RPR.0534.1.0.UJA10.OP.DC0060" ,
 "RPR.0534.1.0.UJA10.TP.DC0094" ,
 "RPR.0534.1.0.UJA10.TP.DC0193" ,
 "RPR.0534.1.0.UMA.TM.DF0001" ,
 "RPR.0534.1.0.UMA10.OP.DF0045" ,
 "RPR.0534.1.0.CWA.CWB.CWD.CWE.OP.DC0002" ,
 "RPR.0534.1.0.UJA.OP.DC0015" ,
 "RPR.0534.1.0.UJA.OP.PF0001" ,
 "RPR.0534.1.0.UJA.OP.PF0002" ,
 "RPR.0534.1.0.UJA.TM.DF0002" ,
 "RPR.0534.1.0.UJA.TM.DF0008" ,
 "RPR.0534.1.0.UJA.TM.DF0014" ,
 "RPR.0534.1.0.UJA.TM.DF0041" ,
 "RPR.0534.1.0.UJA.TM.DF0045" ,
 "RPR.0534.1.0.UJA.TM.DF0057" ,
 "RPR.0534.1.0.UJA.TP.DC0075" ,
 "RPR.0534.1.0.UJA10.OP.DC0049" ,
 "RPR.0534.1.0.UJA10.OP.DC0055" ,
 "RPR.0534.1.0.UJA10.OP.DC0056" ,
 "RPR.0534.1.0.UJA10.OP.DC0070" ,
 "RPR.0534.1.0.UJA10.OP.DC0077" ,
 "RPR.0534.1.0.UJA10.OP.DC0085" ,
 "RPR.0534.1.0.UJA10.OP.DC0090" ,
 "RPR.0534.1.0.UJA10.TP.DC0098" ,
 "RPR.0534.1.0.UJA10.TP.DC0214" ,
 "RPR.0534.1.0.UMA.TM.DF0012" ,
 "RPR.0534.1.0.UMA.UJA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.UJA.TP.DC0196" ,
 "RPR.0534.1.0.UMA10.OP.DC0095" ,
 "RPR.0534.1.0.UMA10.OP.DC0143" ,
 "RPR.0534.1.0.UMA10.OP.DC0144" ,
 "RPR.0534.1.0.UMA10.OP.DF0044" ,
 "RPR.0534.1.0.UMA10.TP.DC0042" ,
 "RPR.0534.1.0.UMA10.TP.DC0095" ,
 "RPR.0534.1.0.UMA10.TP.DC0096" ,
 "RPR.0534.1.0.UJA.OP.DC0019" ,
 "RPR.0534.1.0.UJA.OP.PF0003" ,
 "RPR.0534.1.0.UJA.OP.PF0004" ,
 "RPR.0534.1.0.UJA.TM.DF0007" ,
 "RPR.0534.1.0.UJA.TM.DF0034" ,
 "RPR.0534.1.0.UJA.TM.DF0039" ,
 "RPR.0534.1.0.UJA.TM.DF0051" ,
 "RPR.0534.1.0.UJA.TM.DF0052" ,
 "RPR.0534.1.0.UJA.TM.DF0053" ,
 "RPR.0534.1.0.UJA10.OP.DC0053" ,
 "RPR.0534.1.0.UJA10.OP.DC0069" ,
 "RPR.0534.1.0.UJA10.OP.DC0073" ,
 "RPR.0534.1.0.UJA10.OP.DC0075" ,
 "RPR.0534.1.0.UJA10.OP.DC0076" ,
 "RPR.0534.1.0.UJA10.OP.DC0083" ,
 "RPR.0534.1.0.UJA10.OP.DC0091" ,
 "RPR.0534.1.0.UJA10.TP.DC0203" ,
 "RPR.0534.1.0.UJA10.TP.DC0204" ,
 "RPR.0534.1.0.UJA10.TP.DC0205" ,
 "RPR.0534.1.0.UJA10.TP.DC0206" ,
 "RPR.0534.1.0.UJA10.TP.DC0207" ,
 "RPR.0534.1.0.UJA.TP.DC0209" ,
 "RPR.0534.1.0.UJA10.TP.DC0210" ,
 "RPR.0534.1.0.UJA10.TP.DC0212" ,
 "RPR.0534.1.0.UMA.TM.DF0003" ,
 "RPR.0534.1.0.UMA.TM.DF0004" ,
 "RPR.0534.1.0.UJA.OP.DC0004" ,
 "RPR.0534.1.0.UJA.TM.DF0035" ,
 "RPR.0534.1.0.UJA.TM.DF0036" ,
 "RPR.0534.1.0.UJA.TM.DF0037" ,
 "RPR.0534.1.0.UJA.TM.DF0038" ,
 "RPR.0534.1.0.UJA.TM.DF0040" ,
 "RPR.0534.1.0.UJA.TM.DF0042" ,
 "RPR.0534.1.0.UJA.TM.DF0043" ,
 "RPR.0534.1.0.UJA.TM.DF0044" ,
 "RPR.0534.1.0.UJA.TM.DF0047" ,
 "RPR.0534.1.0.UJA.TM.DF0048" ,
 "RPR.0534.1.0.UJA.TM.DF0055" ,
 "RPR.0534.1.0.UJA10.OP.DC0063" ,
 "RPR.0534.1.0.UJA10.OP.DC0064" ,
 "RPR.0534.1.0.UJA10.OP.DC0065" ,
 "RPR.0534.1.0.UJA10.OP.DF0036" ,
 "RPR.0534.1.0.UJA.FCA.OP.DC0002" ,
 "RPR.0534.1.0.UJA.FCJ.OP.DC0001" ,
 "RPR.0534.1.0.UJA.FBB.TP.DC0001" ,
 "RPR.0534.1.0.UKC.UKU.SMK.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LAA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MKF01.OP.DC0001" ,
 "RPR.0534.1.0.UMA.PAH10-50.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LCP10.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LWB.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAY.OP.DC0005" ,
 "RPR.0534.1.0.UMA.MVA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MXN.OP.DC0002" ,
 "RPR.0534.1.0.UMA.MAV.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAY.OP.DC0002" ,
 "RPR.0534.1.0.UMA.MAY.OP.DC0004" ,
 "RPR.0534.1.0.UMA.LAD.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LAH.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LBA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LCC.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LCS.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAY.OP.DC0003" ,
 "RPR.0534.1.0.PAB10-70.OP.DC0001" ,
 "RPR.0534.1.0.UJA.UJE.LBA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LBG10-70.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LCA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LCM10-70.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAJ.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAL.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAY.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MKF50.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MXN.OP.DC0001" ,
 "RPR.0534.1.0.UMA.BN.DC0001" ,
 "RPR.0534.1.0.UMA.PGB.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LAC.OP.DC0001" ,
 "RPR.0534.1.0.UMA.MAA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.TH.DC0010" ,
 "RPR.0534.1.0.UMA.LAA.TH.DC0001" ,
 "RPR.0534.1.0.UMA.LAB.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LAB.TH.DC0001" ,
 "RPR.0534.1.0.UMA.LBG.TH.DC0004" ,
 "RPR.0534.1.0.UMA.LBG.TH.DC0005" ,
 "RPR.0534.1.0.UMA.LCA.TH.DC0003" ,
 "RPR.0534.1.0.UMA.LCC.TH.DC0001" ,
 "RPR.0534.1.0.UMA.LCS.TH.DC0001" ,
 "RPR.0534.1.0.UMA.MKF01.TH.DC0022" ,
 "RPR.0534.1.0.UMA.PCC01.AT.OP.DC0009" ,
 "RPR.0534.1.0.UMA.SGA.TH.DC0009" ,
 "RPR.0534.1.0.URS.SGA.TH.DC0010" ,
 "RPR.0534.1.0.UMA.GCK.TH.DC0001" ,
 "RPR.0534.1.0.UMA.MA&.TH.DC0004" ,
 "RPR.0534.1.0.UMA.MKF50.TH.DC0002" ,
 "RPR.0534.1.0.UMA.QL.TH.DC0001" ,
 "RPR.0534.1.0.UMA.QLC.TH.DC0001" ,
 "RPR.0534.1.0.URA.OP.DC0001" ,
 "RPR.0534.1.0.UMA.LAV.AT.OP.DC0004" ,
 "RPR.0534.1.0.UMA.PEC.AT.OP.DC0001" ,
 "RPR.0534.1.0.UMA.PEC.AT.OP.DC0002" ,
 "RPR.0534.1.0.UMA.PEC.AT.OP.DC0005" ,
 "RPR.0534.1.0.UMA.PEC.AT.OP.DC0006" ,
 "RPR.0534.1.0.UMA.MA&.AT.OP.DC0007" ,
 "RPR.0534.1.0.UMA.MA&.AT.OP.DC0008" ,
 "RPR.0534.1.0.UMA.LCT.AT.OP.DC0015" ,
 "RPR.0534.1.0.UMA.TH.DC0005" ,
 "RPR.0534.1.0.UMA.TH.DC0006" ,
 "RPR.0534.1.0.UMA.TH.DC0007" ,
 "RPR.0534.1.0.UMA.TH.DC0009" ,
 "RPR.0534.1.0.UKC.KLE21-24.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KLA03.OP.DC0001" ,
 "RPR.0534.1.0.UKZ.SAE21.SAE41.OP.DC0001" ,
 "RPR.0534.1.0.URF.11,12SAQ25.OP.DC0001" ,
 "RPR.0534.1.0.URF.11,12SAQ42.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ21.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ21.OP.DC0002" ,
 "RPR.0534.1.0.URF.SAQ21.OP.DC0003" ,
 "RPR.0534.1.0.URF.SAQ22.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ40.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ41.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ42.OP.DC0001" ,
 "RPR.0534.1.0.UJA.KLB01-02.OP.DC0001" ,
 "RPR.0534.1.0.UKC.KLE48.OP.DC0001" ,
 "RPR.0534.1.0.UBN13.OP.DC0007" ,
 "RPR.0534.1.0.UJA.KLA04.OP.DC0001" ,
 "RPR.0534.1.0.UMA10.OP.DC0007" ,
 "RPR.0534.1.0.URF.11,12SAQ41.OP.DC0001" ,
 "RPR.0534.1.0.URF.SAQ27.OP.DC0001"
])
    print("doc_list: ", doc_list_.count())
    for each in doc_list_:
        each.sd_approval.remarks = 'approve'
        each.sd_approval.save()

    page_no = 1
    no_of_items = 200

    search_form = SecondTierReviewSearchForm()

    filter_list = []

    if (request.GET):
        search_form = SecondTierReviewSearchForm(request.GET)

        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('task_id' in each):
                    filter_list.append(Q(**{'task__task_id__icontains': search_form.cleaned_data[each].upper()}))
                if ('title' in each):
                    filter_list.append(Q(**{'task__title__icontains': search_form.cleaned_data[each].upper()}))
                if (each == 'division'):
                    filter_list.append(Q(**{'task__division': search_form.cleaned_data[each]}))
                if (each == 'department'):
                    filter_list.append(Q(**{'task__dept_id': search_form.cleaned_data[each]}))
                if (each == 'committee'):
                    filter_list.append(Q(**{'committee': search_form.cleaned_data[each]}))
                if (each == 'div_head_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'division_head_approval__isnull': value}))
                if (each == 'chief_engr_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'chief_eng_approval__isnull': value}))
                if (each == 'sd_recommendation'):
                    if search_form.cleaned_data[each] != "":
                        value = True
                        if search_form.cleaned_data[each] == "Yes":
                            value = False
                        filter_list.append(Q(**{'sd_approval__isnull': value}))

    if (len(filter_list) > 0):
        doc_list = SecondTierDocumentReview.objects.filter(task__created_date__lt='2025-07-31', sd_approval__remarks__isnull=False).filter(reduce(operator.and_, filter_list)).annotate(count=Count('committee_approval')).order_by('-count')
    else:
        doc_list = SecondTierDocumentReview.objects.filter(task__created_date__lt='2025-07-31', sd_approval__remarks__isnull=False).annotate(count=Count('committee_approval')).order_by('-count')

    total_reviews = len(doc_list)

    # for download list as excel
    if (request.GET.get('download')):
        if (request.GET.get('download') == 'excel'):
            print("Send CSV report")
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="committee_recommendation_list.csv"'
            writer = csv.writer(response)
            writer.writerow(
                ["Task", "Title", "Division", "Department/Shop", "Committee", "Assigned Date", "Deadline",
                 "Div Head Recommendation", "CE Recommendation", "SD Recommendation"])
            for each in doc_list:
                row = []
                row.append(each.task)
                row.append(each.task.title)
                row.append(each.task.division)
                row.append(each.task.dept_id)
                row.append(each.committee)
                row.append(each.assigned_date)
                row.append(each.committee_deadline)
                if(each.division_head_approval == None):
                    row.append("")
                else:
                    row.append(each.division_head_approval.remarks)
                if(each.chief_eng_approval == None):
                    row.append("")
                else:
                    row.append(each.chief_eng_approval.remarks)
                if(each.sd_approval == None):
                    row.append("")
                else:
                    row.append(each.sd_approval.remarks)
                writer.writerow(row)
            return response


    paginator = Paginator(doc_list, no_of_items)

    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))
    try:
        doc_list = paginator.page(page_no)

    except PageNotAnInteger:
        doc_list = paginator.page(page_no)

    except EmptyPage:
        doc_list = paginator.page(paginator.num_pages)

    context = {
            'doc_list': doc_list,
            'total_reviews': total_reviews,
            'form': search_form,
    }

    return render(request, 'document_review/pms_second_tier_doc_review_list.html', context)



def second_tier_doc_review(request, action=None, id=None):

    doc_list = SecondTierDocumentReview.objects.filter(assigned_date__gt='2025-07-31').filter(committee__members=request.user)
    doc_list_as_head = SecondTierDocumentReview.objects.filter(assigned_date__gt='2025-07-31').filter(committee__div_head=request.user)

    total_reviews = len(doc_list)+len(doc_list_as_head)

    doc_list = doc_list.union(doc_list_as_head)

    context = {
            'doc_list': doc_list,
            'total_reviews': total_reviews,
    }

    return render(request, 'document_review/second_tier_doc_review.html', context)

def assign_doc_rev_committee(request, doc_id):
    category = request.GET.get('category')
    doc_rev = None

    referer = request.META.get('HTTP_REFERER')
    if (category == 'Operational'):
        doc_rev = OperationalDocumentReview.objects.get(id=doc_id)
        if (SecondTierDocumentReview.objects.filter(op_doc_review=doc_rev).count() > 0):
            context = {'doc_rev':doc_rev, "already_assigned":True}
            return render(request, 'document_review/assign_doc_rev_committee.html', context=context)

    if (category == 'Regulation'):
        doc_rev = RegulationDocumentReview.objects.get(id=doc_id)
        if (SecondTierDocumentReview.objects.filter(regulation_doc_review=doc_rev).count() > 0):
            context = {'doc_rev':doc_rev, "already_assigned":True}
            return render(request, 'document_review/assign_doc_rev_committee.html', context=context)

    if (category == 'Fire'):
        doc_rev = FireAndEmergencyDocumentReview.objects.get(id=doc_id)
        if (SecondTierDocumentReview.objects.filter(fire_doc_review=doc_rev).count() > 0):
            context = {'doc_rev':doc_rev, "already_assigned":True}
            return render(request, 'document_review/assign_doc_rev_committee.html', context=context)

    if (category == 'Other'):
        doc_rev = OthersDocumentReview.objects.get(id=doc_id)
        if (SecondTierDocumentReview.objects.filter(other_doc_review=doc_rev).count() > 0):
            context = {'doc_rev':doc_rev, "already_assigned":True}
            return render(request, 'document_review/assign_doc_rev_committee.html', context=context)

    form = DocRevAssignCommittee(initial={'doc_rev': doc_rev,'category': category})

    context = {'form': form, 'doc_rev':doc_rev}

    context.update({"redirect": referer})
    if(request.method == 'POST'):
        form = DocRevAssignCommittee(request.POST,initial={'doc_rev': doc_rev, 'category': category})
        if(form.is_valid()):
            second_tier_rev = form.save(commit=False)
            second_tier_rev.assigned_date = datetime.date.today()
            second_tier_rev.committee_deadline = datetime.date.today()+datetime.timedelta(days=4)
            second_tier_rev.task = doc_rev.task
            second_tier_rev.category = doc_rev.category()
            second_tier_rev.save()
            # TODO: send mail to committee members about doc rev assignment
            notify = threading.Thread(target=committee_mailer, args=(second_tier_rev,))
            notify.start()
            context.update({'success': True})
            referrer = request.POST.get('referrer')
            if(not referrer):
                referrer = "task_management/document_review/list_review_report"
            context.update({'referrer': referrer})
        else:
            context.update({'form': form})

    return render(request,'document_review/assign_doc_rev_committee.html',context=context)

def committee_mailer(second_tier_rev):
    committee = second_tier_rev.committee
    subject = "Second Tier Review of Document: {}".format(second_tier_rev.task)
    msg_body = "Review of Document: {} is assigned to your committee for second tier feedback & recommendations.".format(second_tier_rev.task)
    receiver_email = committee.lead.username
    members = committee.members.all()
    members = members.exclude(username=receiver_email).values_list('username', flat=True)
    CC = list(members)
    send_email_with_cc(msg_body, subject=subject, receiver_email=receiver_email, CC=CC)

def open_doc_rev_by_committee(request, id):

    committe_rev = SecondTierDocumentReview.objects.get(id=id)
    if(request.user.profile.access_level > 2 and request.user.has_perm('task_management.view_secondtierdocumentreview') == False):
        if (not request.user in committe_rev.committee.members.all()):
            if(request.user != committe_rev.committee.div_head):
                return HttpResponse("You are not a member of the Second Tier committee of this Document!")
    category = committe_rev.category
    feed_back = None
    form = None
    if (category == 'Operational'):
        feed_back = committe_rev.op_doc_review
        form = OperationalDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Regulation'):
        feed_back = committe_rev.regulation_doc_review
        form = RegulationDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Fire'):
        feed_back = committe_rev.fire_doc_review
        form = FireAndEmergencyDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Other'):
        feed_back = committe_rev.other_doc_review
        form = OthersDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})

    committee_rev_cmnt = DocumentReviewComments.objects.filter(second_tier_committee_review_id=id)

    task_comment_list = Comment.objects.filter(task_id=committe_rev.task).order_by('-created_date')

    context = {
        'form': form,
        'feedback': feed_back,
        'task':feed_back.task,
        'committee_rev': committe_rev,
        'committee_rev_cmnt': committee_rev_cmnt,
        'task_comment_list': task_comment_list,
    }
    return render(request, 'document_review/committee_view_doc_feedback.html', context=context)


def pms_open_doc_rev_by_committee(request, id):

    committe_rev = SecondTierDocumentReview.objects.get(id=id)
    if(request.user.profile.access_level > 2 and request.user.has_perm('task_management.view_secondtierdocumentreview') == False):
        if (not request.user in committe_rev.committee.members.all()):
            if(request.user != committe_rev.committee.div_head):
                return HttpResponse("You are not a member of the Second Tier committee of this Document!")
    category = committe_rev.category
    feed_back = None
    form = None
    if (category == 'Operational'):
        feed_back = committe_rev.op_doc_review
        form = OperationalDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Regulation'):
        feed_back = committe_rev.regulation_doc_review
        form = RegulationDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Fire'):
        feed_back = committe_rev.fire_doc_review
        form = FireAndEmergencyDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Other'):
        feed_back = committe_rev.other_doc_review
        form = OthersDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})

    committee_rev_cmnt = DocumentReviewComments.objects.filter(second_tier_committee_review_id=id)

    task_comment_list = Comment.objects.filter(task_id=committe_rev.task).order_by('-created_date')

    context = {
        'form': form,
        'feedback': feed_back,
        'task':feed_back.task,
        'committee_rev': committe_rev,
        'committee_rev_cmnt': committee_rev_cmnt,
        'task_comment_list': task_comment_list,
    }
    return render(request, 'document_review/pms_committee_view_doc_feedback.html', context=context)

def committee_recomendation(request, id):

    committe_rev = SecondTierDocumentReview.objects.get(id=id)
    if (request.user.profile.access_level > 2):
        if (not request.user in committe_rev.committee.members.all()):
            if (request.user != committe_rev.committee.div_head):
                return HttpResponse("You are not a member of the Second Tier committee of this Document!")
    category = committe_rev.category
    feed_back = None

    if (category == 'Operational'):
        feed_back = committe_rev.op_doc_review
    if (category == 'Regulation'):
        feed_back = committe_rev.regulation_doc_review
    if (category == 'Fire'):
        feed_back = committe_rev.fire_doc_review
    if (category == 'Other'):
        feed_back = committe_rev.other_doc_review
    # if (committe_rev.committee_approval.filter(signed_by=request.user).exists()):
    #     return HttpResponse("You have already recommended the initial review of this Document!")

    if(request.user.username == 'md@npcbl.gov.bd'):
        form = ApprovalSignatureForm_MD()
    else:
        form = ApprovalSignatureForm()

    context = {
        'form': form,
        'feedback': feed_back,
        'task': feed_back.task,
        'committee_rev': committe_rev,
    }
    if(request.method == 'POST'):
        if(request.user.username == 'md@npcbl.gov.bd'):
            form = ApprovalSignatureForm_MD(request.POST)
        else:
            form = ApprovalSignatureForm(request.POST)

        if(form.is_valid()):
            try:
                approval = form.save(commit=False)
                approval.sign_hash = request.user.profile.signature
                approval.signed_by = request.user
                approval.signed_on = datetime.datetime.today()
                approval.save()

                # Notify MD's approval comment to reviewers
                if(request.POST.get('comment_notify')):
                    notify_reviewer = request.POST.get('comment_notify')
                    if(notify_reviewer == 'first_tier'):
                        reviewer = User.objects.get(email=feed_back.user)

                        # send notification
                        msg_body = request.POST.get('comments')
                        notify = threading.Thread(target=doc_review_mail_and_send_sms, args=(msg_body, reviewer, feed_back.task.task_id))
                        notify.start()
                        sleep(2)
                        context.update({'comment_sent': True, 'notify_reviewer': 'First Tier Reviewer'})

                    elif(notify_reviewer == 'second_tier'):
                        committee_members = committe_rev.committee.members.all()

                        # send notification
                        msg_body = request.POST.get('comments')
                        for reviewer in committee_members:
                            notify = threading.Thread(target=doc_review_mail_and_send_sms,
                                                  args=(msg_body, reviewer, feed_back.task.task_id))
                            notify.start()
                        sleep(2)
                        context.update({'comment_sent': True, 'notify_reviewer': 'Second Tier Reviewer'})

                    else:
                        committee_members = committe_rev.committee.members.all() | User.objects.filter(email=feed_back.user)

                        # send notification
                        msg_body = request.POST.get('comments')
                        for reviewer in committee_members:
                            print(reviewer)
                            notify = threading.Thread(target=doc_review_mail_and_send_sms,
                                                  args=(msg_body, reviewer, feed_back.task.task_id))
                            notify.start()
                        sleep(2)
                        context.update({'comment_sent': True, 'notify_reviewer': 'Both (First & Second Tier Reviewers)'})


                if(request.GET.get('recommendation_by')):
                    recommend_by = request.GET.get('recommendation_by')
                    if(recommend_by == 'div_head'):
                        committe_rev.division_head_approval = approval
                    if (recommend_by == 'chief_eng'):
                        if(request.user.username == 'mushfika.ahmed538@rooppurnpp.gov.bd'):
                            committe_rev.chief_eng_approval = approval
                        else:
                            return HttpResponse("Alert! You are not allowed to recommend!")
                    if (recommend_by == 'sd'):
                        if(request.user.username == 'md@npcbl.gov.bd'):
                            committe_rev.sd_approval = approval
                        else:
                            return HttpResponse("Alert! You are not allowed to approve document!")
                else:
                    committe_rev.committee_approval.add(approval)

                committe_rev.save()
                context.update({'success': True})
            except Exception as e:
                return HttpResponse(e.__str__())

    if (request.user.username == 'md@npcbl.gov.bd'):
        return render(request, 'document_review/second_tier_recommendation_MD.html', context=context)
    else:
        return render(request, 'document_review/second_tier_recommendation.html', context=context)


def committee_review_comment(request, id):
    form = DocumentReviewCommentsForm()

    second_tier = SecondTierDocumentReview.objects.get(id=id)
    review_comments = DocumentReviewComments.objects.filter(second_tier_committee_review=second_tier)
    context = {
        'form': form,
        'committee_rev_cmnt': review_comments,
        'doc_rev':second_tier,
    }

    if (request.method == 'POST'):
        form = DocumentReviewCommentsForm(request.POST)

        if (form.is_valid()):
            comment_submission = form.save(commit=False)
            comment_submission.proposed_by = request.user
            comment_submission.created_at = datetime.datetime.now()
            comment_submission.task = second_tier.task
            comment_submission.second_tier_committee_review = second_tier
            comment_submission.save()
            context.update({'success': True})

    return render(request, 'document_review/committee_review_comment.html', context=context)


# def MD_review_comment(request, id):
#     form = DocumentReviewCommentsForm_MD()
#
#     second_tier = SecondTierDocumentReview.objects.get(id=id)
#     review_comments = DocumentReviewComments.objects.filter(second_tier_committee_review=second_tier)
#     context = {
#         'form': form,
#         'committee_rev_cmnt': review_comments,
#         'doc_rev': second_tier,
#     }
#
#     if (request.method == 'POST'):
#         form = DocumentReviewCommentsForm_MD(request.POST)
#
#         if (form.is_valid()):
#             comment_submission = form.save(commit=False)
#             comment_submission.remarks_by = request.user
#             comment_submission.created_at = datetime.datetime.now()
#             comment_submission.task = second_tier.task
#             comment_submission.second_tier_committee_review = second_tier
#             comment_submission.save()
#             context.update({'success': True})
#
#     return render(request, 'document_review/md_review_comment.html', context=context)


def edit_review_comment(request, id):
    rev_comment = DocumentReviewComments.objects.get(id=id)
    if(rev_comment.proposed_by == request.user or request.user.is_superuser):
        form = DocumentReviewCommentsForm(instance=rev_comment)
        context = {'form':form}
        if(request.method == 'POST'):
            form = DocumentReviewCommentsForm(request.POST,instance=rev_comment)
            if(form.is_valid()):
                form.save()
                context.update({'form': form})
                context.update({'success':True})
            else:
                context.update({'form':form})
        return render(request, 'document_review/committee_review_comment.html', context=context)

    else:
        return HttpResponse("You don't have permission to edit this Review Comment!")

def download_committee_review(request, id):
    committee_rev = SecondTierDocumentReview.objects.get(id=id)
    category = committee_rev.category
    feed_back = None
    form = None
    if (category == 'Operational'):
        feed_back = committee_rev.op_doc_review
        form = OperationalDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Regulation'):
        feed_back = committee_rev.regulation_doc_review
        form = RegulationDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Fire'):
        feed_back = committee_rev.fire_doc_review
        form = FireAndEmergencyDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Other'):
        feed_back = committee_rev.other_doc_review
        form = OthersDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})

    committee_rev_cmnt = DocumentReviewComments.objects.filter(second_tier_committee_review_id=id)

    no_pdf = False

    for each in committee_rev_cmnt:
        print(len(each.proposed_text),len(each.original_text),len(each.remarks))
        if(len(each.proposed_text)> 2200 or len(each.original_text)>2200 or len(each.remarks)>2200):
            no_pdf = True

    npcbl_logo_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'npcbl.png'
    )

    context = {
        'form': form,
        'feedback': feed_back,
        'task': feed_back.task,
        'committee_rev': committee_rev,
        'committee_rev_cmnt': committee_rev_cmnt,
        'host':request.get_host(),
        'unit': str(feed_back.task).split('.')[2],
        'npcbl_logo_path': npcbl_logo_path,
    }
    
    if(no_pdf):
        return render(request, 'document_review/doc_review_complete.html', context=context)
    else:
        #return render(request, 'document_review/doc_review_complete_report.html', context=context)
        template = get_template('document_review/doc_review_complete_report.html')
        context.update({'host': '172.30.31.254'})
        report = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(report.encode(encoding="utf-8",errors='replace')),encoding="utf-8", dest=result)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="doc_rev_' + str(feed_back.task) + '.pdf"'
        return response


def pms_download_committee_review(request, id):
    committee_rev = SecondTierDocumentReview.objects.get(id=id)
    category = committee_rev.category
    feed_back = None
    form = None
    if (category == 'Operational'):
        feed_back = committee_rev.op_doc_review
        form = OperationalDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Regulation'):
        feed_back = committee_rev.regulation_doc_review
        form = RegulationDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Fire'):
        feed_back = committee_rev.fire_doc_review
        form = FireAndEmergencyDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})
    if (category == 'Other'):
        feed_back = committee_rev.other_doc_review
        form = OthersDocumentReviewForm(instance=feed_back, initial={'task': feed_back.task})

    committee_rev_cmnt = DocumentReviewComments.objects.filter(second_tier_committee_review_id=id)

    no_pdf = False

    for each in committee_rev_cmnt:
        print(len(each.proposed_text),len(each.original_text),len(each.remarks))
        if(len(each.proposed_text)> 2200 or len(each.original_text)>2200 or len(each.remarks)>2200):
            no_pdf = True

    npcbl_logo_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'npcbl.png'
    )

    context = {
        'form': form,
        'feedback': feed_back,
        'task': feed_back.task,
        'committee_rev': committee_rev,
        'committee_rev_cmnt': committee_rev_cmnt,
        'host':request.get_host(),
        'unit': str(feed_back.task).split('.')[2],
        'npcbl_logo_path': npcbl_logo_path
    }
    if(no_pdf):
        return render(request, 'document_review/pms_doc_review_complete.html', context=context)
    else:
        template = get_template('document_review/pms_doc_review_complete_report.html')
        context.update({'host': '172.30.31.254'})
        report = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(report.encode(encoding="utf-8",errors='replace')),encoding="utf-8", dest=result)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="doc_rev_' + str(feed_back.task) + '.pdf"'
        return response

def assign_sar_reviewer(request):

    if(not request.user.has_perm('task_management.add_safetyanalysisreportreview')):
        return HttpResponse("You don't have permission to Assign Reviewer!")

    committ_id = None
    if(request.GET.get('committee_id')):
        committ_id = request.GET.get('committee_id')

    form  = SafetyAnalysisReportReviewForm(initial={'assigned_by': request.user,'committee':committ_id})

    list = SafetyAnalysisReportReview.objects.filter(committee__lead=request.user).order_by('committee')
    if(committ_id):
        list = SafetyAnalysisReportReview.objects.filter(committee__lead=request.user,committee__id=committ_id)
    context = {'form': form,'list':list}

    if(request.method == 'POST'):
        form = SafetyAnalysisReportReviewForm(request.POST, initial={'assigned_by': request.user})
        if(form.is_valid()):
            form.save(commit=False)
            form.assigned_by = request.user
            sar = form.save()
            sar.save()
            #TODO: send mail to reviewer
            threading.Thread(target=notify_sar_reviewer, args=(sar,)).start()
            context.update({'success':'success'})
            new_form = SafetyAnalysisReportReviewForm(initial={'assigned_by': request.user,'committee':committ_id})
            context.update({'form': new_form})
        else:
            context.update({'form': form})

    return render(request,'document_review/assign_sar_reviewer.html', context)

def notify_sar_reviewer(sar):
    print("SAR Reviewer Notify")
    subject = "Safety Analysis Document Review, Section: {}".format(sar.assigned_section)
    body = ("You're assigned to review a part of Safety Analysis Report, Section: {}, Title: {}.\n "
            "Prepare your review report in a word file and upload the file to PMS ").format(sar.assigned_section,sar.assigned_section_title)
    send_email_only(msg_body=body, subject=subject, receiver_email=sar.user.email)

def delete_sar_reviewer(request,sar_id):
    sar = SafetyAnalysisReportReview.objects.get(id=sar_id)
    if(request.user != sar.committee.lead):
        return HttpResponse("You don't have permission to remove the SAR Reviewer!")
    sar.delete()

    return redirect('/task_management/document_review/assign_sar_reviewer')

def my_sar_review_list(request):
    sar_list = SafetyAnalysisReportReview.objects.filter(user=request.user)
    context = {'sar_list': sar_list}
    return render(request,'document_review/assigned_sar_list.html', context)

def upload_sar_individual_report(request,id):
    sar = SafetyAnalysisReportReview.objects.get(id=id)

    if (request.user != sar.user):
        return HttpResponse("You don't have permission to upload report for this Section!")
    context = {'sar': sar}

    #TODO: handle post request, upload file to ftp

    if (request.method == 'POST'):
        if (sar.analysis_report_file):
            existnig_report = File.objects.get(hash=sar.analysis_report_file)
            existnig_report.delete()
        report = request.FILES['sar_idv_report']
        hash = request.POST.get('sar_idv_report_hash')
        file_name = str(id) + "_" + report.name
        try:
            server_url = upload_to_ftp(report.file, file_name)
            file = File.objects.create(file_name=file_name, hash=hash, server_loc=server_url, file_size=report.size)
            sar.analysis_report_file = file.hash
            sar.assign_date = datetime.date.today()
            sar.save()
            context.update({'success':'success'})
        except Exception as e:
            return HttpResponse("Failed, {}".format(e.__str__()))
    return render(request,'document_review/upload_individual_sar.html', context)


def view_sar_indv_report_list(request,committee_lead=None):
    sar_list = SafetyAnalysisReportReview.objects.all().order_by('committee')
    if(committee_lead):
        sar_list = sar_list.filter(committee__lead=committee_lead)
    context = {'sar_list': sar_list}
    return render(request, 'document_review/all_sar_list.html', context)

def upload_committee_report(request,id=None):
    sar_list = SafetyAnalysisReportCommittee.objects.filter(lead=request.user)
    context = {'sar_list': sar_list}

    if(id):
        initial = {'committee':id}
        form = SARCommitteeReportForm(initial=initial)
        context = {'form': form}

        if(request.method == 'POST'):
            old_report= None
            old_report_hash = None
            if(SARCommitteeReport.objects.filter(committee_id=id).count()>0):
                old_report = SARCommitteeReport.objects.get(committee_id=id)

            form = SARCommitteeReportForm(request.POST,initial=initial)
            if(old_report):
                form = SARCommitteeReportForm(request.POST,instance=old_report, initial=initial)
                old_report_hash = old_report.analysis_report_file
            if(form.is_valid()):
                try:
                    report = request.FILES['sar_committee_report']
                    hash = request.POST.get('sar_committee_report_hash')
                    file_name = str(id) + "_" + report.name
                    committee_report = form.save(commit=False)
                    server_url = upload_to_ftp(report.file, file_name)
                    file = File.objects.create(file_name=file_name, hash=hash, server_loc=server_url, file_size=report.size)
                    committee_report.analysis_report_file = file.hash
                    committee_report.submitted_by = request.user
                    committee_report.submitted_on = datetime.datetime.now()
                    committee_report.save()
                    #delete old report
                    if(old_report):
                        f = File.objects.get(hash=old_report_hash)
                        f.delete()
                    context.update({'success': 'success'})
                except Exception as e:
                   return HttpResponse("Failed to Upload Committee Report, {}".format(e.__str__()))
    return render(request,'document_review/sar_committee_report.html',context=context)

def view_sar_committee_report(request,id=None):
    committee_reports = SafetyAnalysisReportCommittee.objects.all()
    context = {'sar_list': committee_reports}
    return render(request,'document_review/sar_committee_report.html', context)


def change_document_recommendation(request, id):
    approval_signature = ApprovalSignature.objects.get(id=id)
    form = ApprovalSignatureForm(instance=approval_signature)
    str_id = request.GET.get('second_tier_id')
    committe_rev = SecondTierDocumentReview.objects.get(id=str_id)
    if (request.user.profile.access_level > 2):
        if (not request.user in committe_rev.committee.members.all()):
            if (request.user != committe_rev.committee.div_head):
                return HttpResponse("You are not a member of the Second Tier committee of this Document!")
    category = committe_rev.category
    feed_back = None

    if (category == 'Operational'):
        feed_back = committe_rev.op_doc_review
    if (category == 'Regulation'):
        feed_back = committe_rev.regulation_doc_review
    if (category == 'Fire'):
        feed_back = committe_rev.fire_doc_review
    if (category == 'Other'):
        feed_back = committe_rev.other_doc_review
    context = {
        'form': form,
        'feedback': feed_back,
        'task': feed_back.task,
        'committee_rev': committe_rev,
    }
    if(request.method == 'POST'):
        form = ApprovalSignatureForm(request.POST,instance=approval_signature)
        if(form.is_valid()):
            stat = form.save()
            context.update({'success': True})
    return render(request, 'document_review/second_tier_recommendation.html', context=context)

def second_tier_all_approve(request, id):
    user = request.user
    st_review = SecondTierDocumentReview.objects.filter(division_head_approval__isnull=False)
    if(user.username == 'tanziar.rahman523@rooppurnpp.gov.bd' or 'hasmat.ali782@rooppurnpp.gov.bd' or user.username == 'pd@rooppurnpp.gov.bd'):
        count = 1
        for each in st_review:
            if(each.committee_approval.count()<1):
                continue
            remarks = each.division_head_approval.remarks
            date = each.division_head_approval.signed_on
            if(user.username == 'hasmat.ali782@rooppurnpp.gov.bd'):
                if(not each.chief_eng_approval):
                    approval = ApprovalSignature.objects.create(signed_on=date, remarks=remarks, signed_by=user, sign_hash=user.profile.signature)
                    each.chief_eng_approval = approval
                    count+=1
                    each.save()
                else:
                    if(each.chief_eng_approval.remarks != remarks):
                        each.chief_eng_approval.remarks = remarks
                        count += 1
                        each.chief_eng_approval.save()

            if(user.username == 'pd@rooppurnpp.gov.bd'):
                if (not each.sd_approval):
                    approval = ApprovalSignature.objects.create(signed_on=date, remarks=remarks, signed_by=user, sign_hash=user.profile.signature)
                    each.sd_approval = approval
                    count += 1
                    each.save()
                else:
                    if(each.sd_approval.remarks != remarks):
                        each.sd_approval.remarks = remarks
                        count += 1
                        each.sd_approval.save()

        response_msg = str(count)+" Recommendation Given"

        return HttpResponse(response_msg)
    else:
        return HttpResponse("You're not allowed to perform this operation")
