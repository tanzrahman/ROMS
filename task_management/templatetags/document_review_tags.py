from task_management.models import *
from task_management.forms_doc_review import approvalChoiceList
from django import template

register = template.Library()

@register.filter(name='has_approval_from')
def has_approval_from(approval_list,user):
    if (approval_list.filter(signed_by=user).count()>0):
        approval =  approval_list.filter(signed_by=user).first()
        return approval.remarks
    else:
        return None


@register.filter(name='remarks_display_str')
def remarks_display_str(remarks):
    if(remarks == ""):
        return remarks
    for each in approvalChoiceList:
        if (each[0] == remarks):
            return each[1]
    return ""

# @register.filter(name='remarks_display_str_MD')
# def remarks_display_str(remarks):
#     if(remarks == ""):
#         return remarks
#     for each in approvalChoiceList_MD:
#         if (each[0] == remarks):
#             return each[1]
#     return ""

@register.filter(name='get_sar_committ_report')
def get_sar_committee_report(committee):

    if(SARCommitteeReport.objects.filter(committee=committee).count()>0):
        return SARCommitteeReport.objects.get(committee=committee)
    return None

@register.filter(name='is_chief_eng')
def is_chief_eng(user):
    if(user.username == 'mushfika.ahmed538@rooppurnpp.gov.bd'):
        return True

@register.filter(name='is_sd')
def is_sd(user):
    if(user.username == 'md@npcbl.gov.bd'):
        return True

@register.filter(name='extract_version_info')
def extract_version_info(text):
    if('2' in text):
        return 2
    elif('1' in text):
        return 1
