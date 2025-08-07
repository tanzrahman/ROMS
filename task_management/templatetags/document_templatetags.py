from task_management.models import *

from django import template

register = template.Library()


@register.filter(name='has_no_document_request')
def has_no_document_request(task, user):
    if (DocumentRequest.objects.filter(task=task, requested_by=user).count() > 0):
        return False
    else:
        return True


@register.filter(name='get_doc_request_status')
def get_doc_request_status(doc_request_id):
    req = DocumentRequest.objects.get(id=doc_request_id)

    if (req.approval_level == 1):
        return "Send For Approval"
    if (req.approval_level == 2):
        return "Send to Documentation Dept"
    if (req.approval_level == 3):
        return "Document Provided"
    if (req.approval_level == -1):
        return "Document Not Available at Documentation Dept"


@register.filter(name='get_document_request')
def get_document_request(task_id, user):
    reqs = DocumentRequest.objects.filter(task__id=task_id, task__supervisor=user, requested_by__profile__division=user.profile.division).exclude(requested_by=user)
    if(reqs.count()>0):
        for each in reqs:
            if(each.approval_level == 1):
                return each.id
    else:
        return None


@register.filter(name='doc_request_count')
def doc_request_count(uid):
    return DocumentRequest.objects.filter(requested_by_id=uid).count()

@register.filter(name='split_recipients')
def split_recipients(recepients):
    trimmed = recepients[0:256]
    total = len(recepients.split(','))-1
    trimmed = trimmed + "  (total: "+str(total)+")"
    return trimmed

@register.filter(name="committe_assgined")
def committe_assgined(rev):

    if(rev.category() == "Operational"):
        if(SecondTierDocumentReview.objects.filter(op_doc_review=rev).count() > 0):
            return True
    if (rev.category() == "Regulation"):
        if (SecondTierDocumentReview.objects.filter(regulation_doc_review=rev).count() > 0):
            return True
    if(rev.category() == "Fire"):
        if (SecondTierDocumentReview.objects.filter(fire_doc_review=rev).count() > 0):
            return True
    if (rev.category() == "Other"):
        if (SecondTierDocumentReview.objects.filter(other_doc_review=rev).count() > 0):
            return True
    return False

@register.filter(name="get_doc_rev_id")
def get_doc_rev_id(rev):

    if(rev.category == "Operational"):
        return rev.op_doc_review.id
    if (rev.category == "Regulation"):
        return rev.regulation_doc_review.id
    if(rev.category == "Fire"):
        return rev.fire_doc_review.id
    if (rev.category == "Other"):
        return rev.other_doc_review.id
    return False