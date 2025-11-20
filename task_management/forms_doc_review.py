import datetime
import re
from cProfile import label
from dis import Instruction
from django import forms
from django.forms import ModelForm, HiddenInput
from django.utils.translation import gettext_lazy as _
from urllib3 import request

from manpower.fields import ListTextWidget
from manpower.forms import Division, Profile
from functools import reduce
import operator

from manpower.models import Committee, ApprovalSignature, SafetyAnalysisReportCommittee
from task_management.forms import OperationalDocumentReview, User, Division, DepartmentShop, Task
from task_management.forms import RegulationDocumentReview, OthersDocumentReview, FireAndEmergencyDocumentReview
from task_management.models import SecondTierDocumentReview, SafetyAnalysisReportReview, SARCommitteeReport

approvalChoiceList = [("", "Select"), ("approve", "Approved"), ("reject", "Rejected"), ("recommend_to_revise", "Recommend to Revise "), ("no_saw_recommend_to_revise", "SAW Not Completed & Revise Document Required"),
                      ("recommend_to_approve", "Recommend to Approve"), ("no_saw_recommend_to_approve", "SAW Not Complete but Recommend to Approve"),
                      ("saw_not_completed", "SAW Not Completed"),
                      ("accept_with_remarks", "Document can be provisionally accepted considering the review comments"),
                      ("provisionally_accepted", "Provisionally accepted considering the review comments"),
                      ("no_saw_accept_with_remarks", "SAW Not Completed & Document can be provisionally accepted considering the review comments"),
                      ]


# approvalChoiceList_MD = [("","Select"), ("approve","Approved"), ("reject","Rejected"),
#                       ("accept_with_remarks","Provisionally accepted considering the review comments"),
#                       ]

#("provisional_acceptance_with_remarks","Document can be provisionally accepted with incorporating the comments provided during review")

def get_approval_list():
    new_approvalChoiceList = []
    for each in approvalChoiceList:
        if (each[0] != 'saw_not_completed' and each[0] != 'recommend_to_revise' and each[0] != 'no_saw_recommend_to_revise' and each[0] != 'approve'and each[0] != 'reject' and each[0] != 'provisionally_accepted'):
            new_approvalChoiceList.append(each)
    return new_approvalChoiceList

def get_approval_list_MD():
    new_approvalChoiceList = []
    for each in approvalChoiceList:
        if (each[0] == '' or each[0] == 'approve' or each[0] == 'reject' or each[0] == 'provisionally_accepted'):
            new_approvalChoiceList.append(each)
    print(new_approvalChoiceList)
    return new_approvalChoiceList

class OperationalDocumentReviewForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none(), label='Document Code')
    ######QUESTIONS#########
    version_of_doc = forms.CharField(required=False, label="Mention the version no of the document")
    eqipment_passport_code = forms.CharField(required=False, label="Equipment passport code")
    manufacturer_of_equipment = forms.CharField(required=False, label="Manufacturer of the equipment")
    safety_class = forms.CharField(required=False, label="Safety Class of the Equipment")
    quality_category = forms.CharField(required=False, label="Quality Category")
    seismic_category = forms.CharField(required=False, label="Seismic Category")
    acceptance_criteria = forms.CharField(required=False, label="Mention the important criteria of the acceptance test of the equipment",
                                          widget=forms.Textarea(attrs=
                                          {
                                              'class': 'form-control',
                                              'placeholder': "for example; KKS Code, reflection of factory documentations, description of equipment premises,"
                                                             " route, reflection of As Built Documentation,reflection of update/modification during SAW,"
                                                             " any aspects for previous non-conformities"
                                          }))
    monitored_params = forms.CharField(required=False,
                                       label="Mention the monitored parameters/success criteria of SAW programs",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    params_reflected = forms.CharField(required=False, label="Are the monitored parameters reflected in the operational documentation?",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    focusing_params = forms.CharField(required=False, label="Which parameters operators have to focus most during the operation?",
                                      widget=forms.Textarea(attrs={'class': 'form-control'})
                                      )

    safety_measures = forms.CharField(required=False, label="Mention the Safety measures to take during the operation",
                                      widget=forms.Textarea(attrs={'class': 'form-control'}))

    developed_for_rnpp = forms.CharField(required=False, label="Are the above documents developed focusing Rooppur NPP? Justify your answer",
                                         widget=forms.Textarea(attrs={'class': 'form-control'}))

    transient_situation_explanation = forms.CharField(required=False,
                                                      label="What kind of transient situation the operational document addressed. Explain the sufficiency of transient situations",
                                                      widget=forms.Textarea(attrs={'class': 'form-control'}))

    fulfill_design_requirements = forms.CharField(required=False,
                                                  label="Does operational document fulfill the design requirements for equipment and systems? If not, explain the differences or anomalies in the text box below",
                                                  widget=forms.Textarea(attrs={'class': 'form-control'}))

    operational_modes_reflected = forms.CharField(required=False, label="All Operational modes are reflected as per the design of equipment and systems.",
                                                  widget=forms.Textarea(attrs={'class': 'form-control'}))

    align_with_scope_limit = forms.CharField(required=False,
                                             label="Does operational instruction of equipment and systems align with the scope and limit mentioned in the passport of equipment manufacturer?  ",
                                             widget=forms.Textarea(attrs={'class': 'form-control'}))

    relevant_document_bd = forms.CharField(required=False,
                                           label="Relevant Normative documents of Bangladesh and Normative documents agreed by the General Contract shall be followed strictly in the Operational Document",
                                           widget=forms.Textarea(attrs={'class': 'form-control'}))

    differences_reflected = forms.CharField(required=False,
                                            label="What kind of differences are reflected in the latest version of the document? Effect of the differences in the latest version of the operational document ",
                                            widget=forms.Textarea(attrs={'class': 'form-control'}))

    list_of_maloperations = forms.CharField(required=False, label="List of possible wrong operations and their consequences  ",
                                            widget=forms.Textarea(attrs={'class': 'form-control'}))

    peripherial_important_params = forms.CharField(required=False,
                                                   label="List of important parameters of peripheral system most important for the operation of the equipment. ",
                                                   widget=forms.Textarea(attrs={'class': 'form-control'}))
    general_feedback = forms.CharField(required=False, label="Your Comments and Feedback on the document (if you have any)",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    class Meta:
        model = OperationalDocumentReview
        fields = ['task', 'version_of_doc', 'eqipment_passport_code', 'manufacturer_of_equipment', 'safety_class',
                  'quality_category', 'seismic_category', 'acceptance_criteria', 'monitored_params', 'params_reflected',
                  'focusing_params', 'safety_measures', 'developed_for_rnpp', 'transient_situation_explanation',
                  'fulfill_design_requirements', 'operational_modes_reflected', 'align_with_scope_limit',
                  'relevant_document_bd', 'differences_reflected', 'list_of_maloperations',
                  'peripherial_important_params', 'general_feedback']

    def __init__(self, *args, **kwargs):
        super(OperationalDocumentReviewForm, self).__init__(*args, **kwargs)

        if (kwargs.get('initial')):
            initial = kwargs.get('initial')

            if (initial.get('task')):
                task = initial.get('task')
                self.fields['task'].initial = task
                self.fields['task'].queryset = Task.objects.filter(id=task.id)

class RegulationDocumentReviewForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none(), label='Document Code')
    ######QUESTIONS#########
    version_of_doc = forms.CharField(required = False)
    storing_entity = forms.CharField(required=False, label="Who will store the documents?", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder':"Responsible person and/or department who will store the document"}))
    effective_date = forms.DateField(required = False, widget=forms.DateInput(attrs={'type': 'date'}))
    next_review_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    next_review_dept_person = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control'}), label="Responsible person and/or department for next review")

    is_applicable = forms.CharField(required = False, widget=forms.Textarea(attrs={'class': 'form-control'}),
                                    label="Check the Regulations, Normative documents (is it developed for Bangladesh?)")
    specific_users_of_document = forms.CharField(required = False,
                                                 label="Specific users of the document",
                                    widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder':"Which department mainly use the document?"}))

    other_users_of_document = forms.CharField(required = False, widget=forms.Textarea(attrs={'class': 'form-control'}),
                                              label="List of Other departments and personnel(designation) will be involved with the document")

    user_qualification = forms.CharField(required = False, widget=forms.Textarea(attrs={'class': 'form-control'}),
                                         label="Qualification of the Users who will use the document")

    safety_measures = forms.CharField(required = False, label="Safety Measures",
                                      widget=forms.Textarea(attrs={'class': 'form-control'}))

    record_of_work = forms.CharField(required = False,
                                     label="Record of Work and distribution of the record to other relevant department",
                                     widget=forms.Textarea(
        attrs={'class': 'form-control', 'placeholder':"Who will keep track of the working records and which departments will get a copy of the record"}))

    deviation_notification_reporting = forms.CharField(required = False,
                                                       label="Deviation Notification and Reporting",
                                                       widget=forms.Textarea(
                                                           attrs={'class': 'form-control',
                                                                  'placeholder':"Who will notify the deviation to relevant personnel and department, and how notification will be done"}))


    test_procedures_valid_logical = forms.CharField(required = False,
                                                    label="Is the Tests/Procedures are valid/logical for Bangladesh?",
                                                    widget=forms.Textarea(attrs={'class': 'form-control'}))

    limits_of_normal_operations = forms.CharField(required = False,
                                                  label="What are the limits of normal condition/operation/parameter and what is the maximum permissible limit?",
                                                  widget=forms.Textarea(attrs={'class': 'form-control'}))

    reason_to_keep_gost_docs = forms.CharField(required = False,
                                               label="Check the term “GOST” and explain the reason to keep/delete/replace",
                                               widget=forms.Textarea(
                                                   attrs={'class': 'form-control',
                                                          'placeholder':'Check if the document has any reference to GOST and explain the reason to keep/delete/replace the reference'
                                                          }))
    general_feedback = forms.CharField(required=False, label="Your Comments and Feedback on the document (if you have any)",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    class Meta:
        model = RegulationDocumentReview
        fields = ['task', 'version_of_doc', 'effective_date','next_review_date', 'next_review_dept_person', 'storing_entity', 'is_applicable', 'specific_users_of_document',
                   'other_users_of_document', 'user_qualification', 'safety_measures', 'record_of_work', 'deviation_notification_reporting',
                   'test_procedures_valid_logical', 'limits_of_normal_operations', 'reason_to_keep_gost_docs', 'general_feedback']

    def __init__(self, *args, **kwargs):
        super(RegulationDocumentReviewForm, self).__init__(*args, **kwargs)

        if (kwargs.get('initial')):
            initial = kwargs.get('initial')

            if (initial.get('task')):
                task = initial.get('task')
                self.fields['task'].initial = task
                self.fields['task'].queryset = Task.objects.filter(id=task.id)


class OthersDocumentReviewForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none(), label='Document Code')
    document_category = forms.CharField(required=False, label='What Type of document is it?')
    version_of_doc = forms.CharField(required=False, label='Version of Document')
    effective_date = forms.DateField(required=False, label='Effective Date', widget=forms.DateInput(attrs={'type': 'date'}))
    storing_entity = forms.CharField(required=False, label="Who will store the document(Dept/Shop)",
                                     widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}))
    for_bd = forms.CharField(required=False, label='Is the document prepared for Bangladesh?',
                                    widget=forms.Textarea( attrs={'class': 'form-control',
                                                'placeholder': 'Does the content of the document comply with Bangladeshi standard practices/regulation?'}))

    users_of_document = forms.CharField(required=False, label="Who (department/ personnel designation) will be the main users of the document?",
                                        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}))
    general_feedback = forms.CharField(required=False, label="Your Comments and Feedback on the document",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    class Meta:
        model = OthersDocumentReview
        fields = ['task', 'document_category', 'version_of_doc', 'effective_date', 'storing_entity', 'for_bd', 'users_of_document','general_feedback']

    def __init__(self, *args, **kwargs):
        super(OthersDocumentReviewForm, self).__init__(*args, **kwargs)
        if (kwargs.get('initial')):
            initial = kwargs.get('initial')
            if (initial.get('task')):
                task = initial.get('task')
                self.fields['task'].initial = task
                self.fields['task'].queryset = Task.objects.filter(id=task.id)


class FireAndEmergencyDocumentReviewForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none(), label='Document Code')
    ######QUESTIONS#########
    version_of_doc = forms.CharField(required = False, label='Version of Document')
    equipment_passport_code = forms.CharField(required = False, label='Equipment Passport Code')
    safety_class = forms.CharField(required = False, label='Safety Class')
    quality_category = forms.CharField(required = False,label='Quality Category')
    seismic_category = forms.CharField(required = False,label='Seismic Category')

    hydrant_piping_acceptance_criteria = forms.CharField(required = False, label='Hydrant/Piping Acceptance Test Criteria',
                                                         widget=forms.Textarea(attrs={'class': 'form-control'}))

    success_criteria_params = forms.CharField(required = False, label='Parameters of success criteria for the system/equipment',
                                              widget=forms.Textarea(attrs={'class': 'form-control'}))

    bangladesh_compliance = forms.CharField(required = False, label='Does design of firefighting system compliance with Bangladesh rules or standard practice in Bangladesh?',
                                            widget=forms.Textarea(attrs={'class': 'form-control'}))

    bd_standard_practice = forms.CharField(required = False,label="Does type of fire execution system used for different area comply with Bangladesh rules or standard practice in Bangladesh?",
                                           widget=forms.Textarea(attrs={'class': 'form-control'}))

    compliance_waste_water_accum = forms.CharField(required = False, label="After execution of fire does waste water/debris accumulation comply with the rules of Bangladesh or standard practice in Bangladesh?",
                                                   widget=forms.Textarea(attrs={'class': 'form-control'}))

    fire_drill_frequency = forms.CharField(required = False, label="How frequent fire mock drill/ emergency drill need to conduct and procedure to conduct is available?",
                                           widget=forms.Textarea(attrs={'class': 'form-control'}))

    steps_need_to_take = forms.CharField(required = False, label="Steps need to take by the initial personnel/ operational person during fire incident is available and if so, then does it satisfactory? Please describe in brief.",
                                         widget=forms.Textarea(attrs={'class': 'form-control'}))

    safety_gear_standards = forms.CharField(required = False, label="Does the safety gears for firefighting is standard for Rooppur NPP?",
                                            widget=forms.Textarea(attrs={'class': 'form-control'}))

    water_level_bd_compliance = forms.CharField(required = False, label="Does the document stated the Minimum water level in tank to maintain as per Bangladesh rules or standard practice in Bangladesh?",
                                                widget=forms.Textarea(attrs={'class': 'form-control'}))

    foam_flooding_scope = forms.CharField(required = False, label="Does the document provide, Procedure of foam flooding and the scope of this system is mentioned for the necessary areas?",
                                          widget=forms.Textarea(attrs={'class': 'form-control'}))

    role_of_personnel = forms.CharField(required = False, label="During emergency situation of fire, the role of different personnel at site is available in the document?",
                                        widget=forms.Textarea(attrs={'class': 'form-control'}))

    align_with_rnpp = forms.CharField(required = False, label="Does instruction of fire and emergency system align with the necessity of Rooppur NPP? ",
                                      widget=forms.Textarea(attrs={'class': 'form-control'}))

    general_feedback = forms.CharField(required = False, label="Your Comments and Feedback on the document",
                                       widget=forms.Textarea(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(FireAndEmergencyDocumentReviewForm, self).__init__(*args, **kwargs)
        if (kwargs.get('initial')):
            initial = kwargs.get('initial')
            if (initial.get('task')):
                task = initial.get('task')
                self.fields['task'].initial = task
                self.fields['task'].queryset = Task.objects.filter(id=task.id)

    class Meta:
        model = FireAndEmergencyDocumentReview
        fields = ['task', 'version_of_doc', 'equipment_passport_code', 'safety_class', 'quality_category', 'seismic_category', 'hydrant_piping_acceptance_criteria',
                  'success_criteria_params', 'bangladesh_compliance', 'bd_standard_practice', 'compliance_waste_water_accum', 'fire_drill_frequency', 'steps_need_to_take',
                  'safety_gear_standards', 'water_level_bd_compliance', 'foam_flooding_scope', 'role_of_personnel', 'align_with_rnpp', 'general_feedback'
                  ]
        

class DocRevAssignCommittee(forms.ModelForm):
    op_doc_review = forms.ModelChoiceField(queryset=OperationalDocumentReview.objects.none(), required=False)
    regulation_doc_review = forms.ModelChoiceField(queryset=RegulationDocumentReview.objects.none(), required=False)
    fire_doc_review = forms.ModelChoiceField(queryset=FireAndEmergencyDocumentReview.objects.none(), required=False)
    other_doc_review = forms.ModelChoiceField(queryset=OthersDocumentReview.objects.none(), required=False)
    committee = forms.ModelChoiceField(queryset=Committee.objects.all())

    class Meta:
        model = SecondTierDocumentReview
        fields = ['op_doc_review', 'regulation_doc_review','fire_doc_review', 'other_doc_review', 'committee']

    def __init__(self, *args, **kwargs):
        super(DocRevAssignCommittee, self).__init__(*args, **kwargs)
        if (kwargs.get('initial')):
            initial = kwargs.get('initial')
            category = initial.get('category')
            doc_rev = initial.get('doc_rev')
            if(category == 'Operational'):
                self.fields['op_doc_review'].queryset = OperationalDocumentReview.objects.filter(id=doc_rev.id)
                self.fields['op_doc_review'].initial = doc_rev
                self.fields['regulation_doc_review'].widget = HiddenInput()
                self.fields['fire_doc_review'].widget = HiddenInput()
                self.fields['other_doc_review'].widget = HiddenInput()

            if(category == 'Regulation'):
                self.fields['regulation_doc_review'].queryset = RegulationDocumentReview.objects.filter(id=doc_rev.id)
                self.fields['regulation_doc_review'].initial = doc_rev
                self.fields['op_doc_review'].widget = HiddenInput()
                self.fields['fire_doc_review'].widget = HiddenInput()
                self.fields['other_doc_review'].widget = HiddenInput()

            if(category == 'Fire'):
                self.fields['fire_doc_review'].queryset = FireAndEmergencyDocumentReview.objects.filter(id=doc_rev.id)
                self.fields['fire_doc_review'].initial = doc_rev
                self.fields['op_doc_review'].widget = HiddenInput()
                self.fields['regulation_doc_review'].widget = HiddenInput()
                self.fields['other_doc_review'].widget = HiddenInput()

            if(category == 'Other'):
                self.fields['other_doc_review'].queryset = OthersDocumentReview.objects.filter(id=doc_rev.id)
                self.fields['other_doc_review'].initial = doc_rev
                self.fields['op_doc_review'].widget = HiddenInput()
                self.fields['regulation_doc_review'].widget = HiddenInput()
                self.fields['fire_doc_review'].widget = HiddenInput()


class ApprovalSignatureForm(forms.ModelForm):
    remarks = forms.ChoiceField(choices=get_approval_list(), required=True, label="Select Your Remarks")
    class Meta:
        model = ApprovalSignature
        fields = ['remarks']

class ApprovalSignatureForm_MD(forms.ModelForm):
    remarks = forms.ChoiceField(choices=get_approval_list_MD(), required=True, label="Select Your Remarks")
    comments = forms.CharField(required=False, label="Comments",
                              widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    class Meta:
        model = ApprovalSignature
        fields = ['remarks', 'comments']

class SafetyAnalysisReportReviewForm(forms.ModelForm):
    committee = forms.ModelChoiceField(queryset=SafetyAnalysisReportCommittee.objects.all(),
                                       required=False, label="Safety Analysis Report Review Committee",
                                       widget=forms.Select(attrs={'class': 'form-control', 'onchange':'load_committee_users(this.options[this.selectedIndex].value)'}),
                                       )
    section = forms.CharField(required=False,label="Section/Chapter assigned to committee",
                              widget=forms.Textarea(attrs={'class': 'form-control','readonly':'true','rows':2}))

    user = forms.ModelChoiceField(queryset=User.objects.all(),required=True, label = "Reviewer")
    assigned_section = forms.CharField(required=True, label="Assigned Sub-section", widget=forms.TextInput(attrs={'class': 'form-control'}))
    assigned_section_title = forms.CharField(required=True, label="Assigned Sub-section Title", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = SafetyAnalysisReportReview
        fields = ['committee','section', 'user', 'assigned_section', 'assigned_section_title']

    def __init__(self, *args, **kwargs):
        super(SafetyAnalysisReportReviewForm, self).__init__(*args, **kwargs)

        if(kwargs.get('initial')):
            assigned_by = kwargs.get('initial').get('assigned_by')
            committee = SafetyAnalysisReportCommittee.objects.filter(lead=assigned_by)
            self.fields['committee'].queryset = committee
            selected_committee = None
            if (kwargs.get('initial').get('committee')):
                selected_committee = kwargs.get('initial').get('committee')
            if(selected_committee):
                selected_committee = SafetyAnalysisReportCommittee.objects.get(id=selected_committee)
                self.fields['committee'].initial = selected_committee
                self.fields['section'].initial = "Section: {}\nTitle: {}".format(selected_committee.sar_section,selected_committee.sar_section_title)
            user_list = SafetyAnalysisReportCommittee.objects.filter(lead=assigned_by).values_list('members', flat=True)
            members = User.objects.filter(id__in=user_list)

            if(selected_committee):
                members = selected_committee.members.all()
            self.fields['user'].queryset = members


class SARCommitteeReportForm(forms.ModelForm):
    committee = forms.ModelChoiceField(queryset=SARCommitteeReport.objects.all(), label='Select Chapter/Section Title', required=True)

    class Meta:
        model = SARCommitteeReport
        fields = ['committee']
    def __init__(self, *args, **kwargs):
        super(SARCommitteeReportForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            committee= kwargs.get('initial').get('committee')
            self.fields['committee'].queryset = SafetyAnalysisReportCommittee.objects.filter(id=committee)