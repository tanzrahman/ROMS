import datetime
import re
from dis import Instruction

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from manpower.fields import ListTextWidget
from manpower.models import Division, Profile
from .models import *
from django.db.models import Q
from functools import reduce
import operator
from django.contrib.auth import backends, get_user_model
from django.contrib.auth.models import Group


TASK_STATUS =(
    ("1", "Created"),
    ("2", "Assigned"),
    ("3", "Completed"),
)

consultancy_request_status =(
    ("all", "All Requests"),
    ("pending", "Pending Requests"),
    ("assigned", "Consultant Assigned"),
)
task_category = (
    ("","ALL"),
    ("SAW","SAW"),
    ("CEW","CEW"),
    ("DocumentReview","DocumentReview"),
)

recommendation = (
    ("", "Select"),
    ("Yes", "Yes"),
    ("No", "No")
)

class DateInput(forms.DateInput):
    input_type = 'date'


def question_list():
    questionList = list(Questions.objects.all().values_list('question', flat= True))
    print(questionList)
    return questionList


class TaskForm(ModelForm):

    task_id = forms.CharField(label='Task ID', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    task_category = forms.CharField(label='Task Category',required=True,initial="CEW")
    milestone_id = forms.CharField(label='Milestone ID', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    stage = forms.CharField(label='Stage',required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    dept_id = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(), label='Department', required=False)
    facility = forms.ModelChoiceField(queryset=Facility.objects.all().order_by('name'), label='Facility', required=False)
    system = forms.ModelChoiceField(queryset=System.objects.all().order_by('name'), label='System', required=False)
    subsystem = forms.ModelChoiceField(queryset=SubSystem.objects.all().order_by('name'), label='Sub-system', required=False)

    relevant_kks_codes = forms.CharField(label='Relevant KKS Code', required=False,
                                         widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    # task_created_by = forms.CharField(label='Task Created by', required=False)
    title = forms.CharField(label='Title', required=False, widget=forms.Textarea(attrs={'rows': 2, 'cols': 50}))
    description = forms.CharField(label='Description', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}))
    planned_start_date = forms.DateField(label='Planned start date', required=False, widget=DateInput)
    planned_end_date = forms.DateField(label='Planned end date', required=False, widget=DateInput)
    actual_start_date = forms.DateField(label='Actual start date', required=False, widget=DateInput)
    actual_end_date = forms.DateField(label='Actual end date', required=False, widget=DateInput)
    percent_completed = forms.IntegerField(label="Percentage Completed", required=False)
    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True),
                                                label="Select Supervisor")
    task_executor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_executor=True),
                                                   label="Select Executor",required=False)
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)

        if (kwargs.get('initial')):
            filter_list = []
            filter_list.append(Q(**{'profile__is_supervisor': True}))
            task_creating_user = kwargs.get('initial').get('creating_user')

            filter_list.append(Q(**{'profile__access_level__gte':task_creating_user.profile.access_level}))


            if (task_creating_user.profile.grade > 3):
                filter_list.append(Q(**{'profile__division': task_creating_user.profile.division}))

            #general rule, show users with lower grade
            #filter_list.append(Q(**{'profile__grade__gte': task_creating_user.profile.grade}))
            #exclude the user himself


            qset = User.objects.filter(reduce(operator.and_,filter_list)).order_by('username')
            if (task_creating_user.profile.access_level < 2):
                qset = User.objects.filter(profile__access_level__gt=3).order_by('username')
            self.fields['supervisor'].queryset = qset

            dept = kwargs['initial'].get('department')
            self.fields['dept_id'].initial = dept

            # if(kwargs['initial'].get('section')):
            #     section = kwargs['initial'].get('section')
            #     filter_list.append(Q(**{'profile__section': section}))
            #
            # if (kwargs['initial'].get('subdepartment')):
            #     sub_dept = kwargs['initial'].get('subdepartment')
            #     filter_list.append(Q(**{'profile__subdepartment': sub_dept}))
            qset = User.objects.filter(profile__division=task_creating_user.profile.division,profile__is_executor=True).order_by('username')
            if(task_creating_user.profile.access_level<2):
                qset = User.objects.filter(profile__access_level__gt=3).order_by('username')
            self.fields['task_executor'].queryset = qset

    class Meta:
        model = Task
        fields = ['facility', 'system', 'subsystem','task_category','milestone_id','task_id','stage','title','description','division','dept_id','relevant_kks_codes',
                  'planned_start_date','planned_end_date','actual_start_date','actual_end_date','percent_completed']
        exclude = ('created_date', 'updated_date','task_created_by','status','is_active')


class TaskEditForm(ModelForm):

    task_id = forms.CharField(label='Task ID', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    milestone_id = forms.CharField(label='Milestone ID', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    stage = forms.CharField(label='Stage',required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    dept_id = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(), label='Department', required=False)
    facility = forms.ModelChoiceField(queryset=Facility.objects.all(), label='Facility', required=False)
    system = forms.ModelChoiceField(queryset=System.objects.all(), label='System', required=False)
    subsystem = forms.ModelChoiceField(queryset=SubSystem.objects.all(), label='Sub-system', required=False)

    relevant_kks_codes = forms.CharField(label='Relevant KKS Code', required=False,
                                         widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    # task_created_by = forms.CharField(label='Task Created by', required=False)
    title = forms.CharField(label='Title', required=False, widget=forms.Textarea(attrs={'rows': 2, 'cols': 50}))
    description = forms.CharField(label='Description', required=False,
                                  widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}))
    planned_start_date = forms.DateField(label='Planned start date', required=False, widget=DateInput)
    planned_end_date = forms.DateField(label='Planned end date', required=False, widget=DateInput)
    # actual_start_date = forms.DateField(label='Actual start date', required=False, widget=DateInput)
    # actual_end_date = forms.DateField(label='Actual end date', required=False, widget=DateInput)
    percent_completed = forms.IntegerField(label="Percentage Completed", required=False)
    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True),
                                                label="Select Supervisor")
    task_executor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_executor=True),
                                                   label="Select Executor",required=False)
    lead_executor = forms.ModelChoiceField(queryset=User.objects.filter(profile__is_executor=True),
                                                   label="Select Lead Executor", required=False)
    def __init__(self, *args, **kwargs):
        super(TaskEditForm, self).__init__(*args, **kwargs)

        if (kwargs.get('initial')):
            filter_list = []
            filter_list.append(Q(**{'profile__is_supervisor': True}))
            task_creating_user = kwargs.get('initial').get('creating_user')



            if (task_creating_user.profile.grade > 2):
                filter_list.append(Q(**{'profile__division': task_creating_user.profile.division}))

            #general rule, show users with lower grade
            #filter_list.append(Q(**{'profile__grade__gte': task_creating_user.profile.grade}))
            #exclude the user himself


            #qset = User.objects.filter(reduce(operator.and_,filter_list)).order_by('username').exclude(username=task_creating_user.username)
            qset = User.objects.filter(reduce(operator.and_, filter_list)).order_by('username')
            if(task_creating_user.profile.access_level < 2):
                qset = User.objects.filter(profile__is_supervisor=True).order_by('username')
            self.fields['supervisor'].queryset = qset

            dept = kwargs['initial'].get('department')
            self.fields['dept_id'].initial = dept

            if(kwargs['initial'].get('section')):
                section = kwargs['initial'].get('section')
                filter_list.append(Q(**{'profile__section': section}))

            if (kwargs['initial'].get('subdepartment')):
                sub_dept = kwargs['initial'].get('subdepartment')
                filter_list.append(Q(**{'profile__subdepartment': sub_dept}))
            qset = User.objects.filter(profile__division=task_creating_user.profile.division).order_by('username').exclude(username=task_creating_user.username)
            if(task_creating_user.profile.access_level < 2):
                qset = User.objects.filter(profile__is_executor=True).order_by('username').exclude(username=task_creating_user.username)
            self.fields['task_executor'].queryset = qset

        if(kwargs.get('instance')):
            instance = kwargs.get('instance')
            self.fields['supervisor'].initial = instance.supervisor.all()
            self.fields['task_executor'].initial = instance.task_executor.all()
            self.fields['milestone_id'].widget.attrs['readonly'] = True
            self.fields['milestone_id'].widget.attrs['class'] = 'readonly_field'
            self.fields['task_id'].widget.attrs['readonly'] = True
            self.fields['task_id'].widget.attrs['class'] = 'readonly_field'
            if(task_creating_user.profile.access_level > 1):
                self.fields['division'].widget.attrs['readonly'] = True
                self.fields['division'].widget.attrs['class'] = 'readonly_field'
                self.fields['division'].queryset = Division.objects.filter(division_name=instance.division)
            if(instance.task_category=='CEW'):
                self.fields['planned_start_date'].widget.attrs['readonly'] = True
                self.fields['planned_start_date'].widget.attrs['class'] = 'readonly_field'
                self.fields['planned_end_date'].widget.attrs['readonly'] = True
                self.fields['planned_end_date'].widget.attrs['class'] = 'readonly_field'
            if(instance.lead_executor):
                le_q = instance.task_executor.all()
                self.fields['lead_executor'].queryset = le_q
                self.fields['lead_executor'].initial = instance.lead_executor
            else:
                le_q = instance.task_executor.all()
                self.fields['lead_executor'].queryset = le_q
                self.fields['lead_executor'].widget.attrs['disabled'] = True
                # self.fields['lead_executor'].widget.attrs['class'] = 'readonly_field'
    class Meta:
        model = Task
        fields = ['facility', 'system', 'subsystem','milestone_id','task_id','stage','title','description','division','dept_id','relevant_kks_codes',
                  'planned_start_date','planned_end_date','percent_completed']
        exclude = ('created_date', 'updated_date','task_created_by','status','is_active')

class ActivityForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        userList = list(User.objects.all().values_list('username', flat= True).order_by('username'))
        self.fields['task_executor'] = forms.CharField(label='Task Executor', required=False, widget=ListTextWidget(data_list=userList, name='task_executor'))

    class Meta:
        model = Activity
        exclude = ('created_date', 'updated_date')


class CommentForm(ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 6, 'cols': 60}), required=True)
    task_id = forms.ModelChoiceField(queryset=Task.objects.none(),required=False)
    def __init__(self,*args,**kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)

        if(kwargs.get('initial')):
            task_id = kwargs.get('initial').get('task_id')
            self.fields['task_id'].queryset = Task.objects.filter(id=task_id)
            self.fields['task_id'].initial = Task.objects.get(id=task_id)

    class Meta:
        model = Comment
        fields = ('task_id', 'comment')


class AddExecutorForm(forms.Form):

    task_id = forms.ModelChoiceField(queryset=Task.objects.none(), label='Task ID', required=False)
    task_executor = forms.ModelMultipleChoiceField(label='Executor', queryset=User.objects.filter(profile__is_executor=True))

    def __init__(self, *args, **kwargs):
        super(AddExecutorForm, self).__init__(*args, **kwargs)

        if(kwargs.get('initial')):
            task_id = kwargs.get('initial').get('task_id')
            print(kwargs.get('initial'))
            self.fields['task_id'].queryset = Task.objects.filter(task_id=task_id)
            self.fields['task_executor'].query_set = User.objects.filter(profile__is_executor=True)


class QuestionsForm(ModelForm):

    class Meta:
        model = Questions
        exclude = ('task',)


class QuestionsAnswersForm(ModelForm):

    task_question = forms.ModelChoiceField(queryset=Questions.objects.none(), label='Question', required=True)
    answer = forms.CharField(label='Answer',widget=forms.Textarea(attrs={'rows':4, 'cols':40}),required=True)
    class Meta:
        model = QuestionsAnswers
        exclude = ('task_id','answered_by', 'created_at','is_approved')

    def __init__(self, *args, **kwargs):
        super(QuestionsAnswersForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            user = kwargs.get('initial').get('user')
            div = user.profile.division
            category = kwargs.get('initial').get('user_category')
            priority = kwargs.get('initial').get('priority')
            qset = Questions.objects.filter(employee_category=category,priority=priority+1)
            self.fields['task_question'].queryset = qset
            self.fields['task_question'].initial = qset.first()

            ques = qset.first()

            if(ques):
                if(ques.category.upper()=='MCQ'):
                    choice_list = [(ques.choice.choice_1,ques.choice.choice_1),(ques.choice.choice_2,ques.choice.choice_2)
                        ,(ques.choice.choice_3,ques.choice.choice_3),(ques.choice.choice_4,ques.choice.choice_4)]

                    self.fields['answer'] = forms.ChoiceField(choices=choice_list,label='Select The right answer',required=True)



class UserSysSubSystemLinkForm(forms.ModelForm):

    user = forms.ModelChoiceField(queryset=User.objects.all(), label='User', required=False)
    system = forms.ModelMultipleChoiceField(queryset=System.objects.all(), label='System', required=False,
                                            widget=forms.CheckboxSelectMultiple)
    sub_system = forms.ModelMultipleChoiceField(queryset=SubSystem.objects.all(), label='SubSystem', required=False,
                                               widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = UserSysSubSystemLink
        fields = '__all__'


class MilestoneSearchForm(forms.Form):
    milestone_id = forms.CharField(required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(),required=False)
    status = forms.ChoiceField(choices=[("",""),("NotStarted","Not Started"),("Performed","Performed"),("Completed", "Completed")], required=False)
    task_id = forms.CharField(required=False)
    system = forms.ModelChoiceField(queryset=System.objects.all(),required=False)
    facility = forms.TypedChoiceField(choices=[("", "")], required=False)
    title = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':1, 'cols':40}))
    start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    is_assigned = forms.ChoiceField(choices=(("",""),('False', 'No'),('True', 'Yes') ), required=False)



    def __init__(self, *args, **kwargs):
        super(MilestoneSearchForm, self).__init__(*args, **kwargs)
        facility = Milestone.objects.filter(status='NotStarted').values_list('facility', flat=True).distinct()
        choice_list = []
        for each in facility:
            choice_list.append((each,each))

        self.fields['facility'].choices = choice_list
        self.fields['facility'].initial = ""

    class Meta:
        fields = ('milestone_id','status', 'task_id', 'system', 'facility_id','title','start_date_from','start_date_to','end_date_from','end_date_to','is_assigned')


class AddPersonForm(forms.Form):
    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.none(), label="Select Supervisor",required=True)
    executor = forms.ModelMultipleChoiceField(queryset=User.objects.none(), label="Select Executor",required=True)
    def __init__(self, *args, **kwargs):
        super(AddPersonForm, self).__init__(*args,**kwargs)
        if(kwargs.get('initial')):

            user = kwargs.get('initial').get('user')
            qset = User.objects.filter(profile__division=user.profile.division, profile__is_supervisor=True).exclude(email=user.email)
            self.fields['supervisor'].queryset = qset
            qset = User.objects.filter(profile__division=user.profile.division, profile__is_executor=True)
            self.fields['executor'].queryset = qset


    # def clean(self):
    #     self.clean()
    #     if(len(self.changed_data['executor'])<1):
    #         raise forms.ValidationError("Must Assign an Executor")
    #     return self


class DivisionSelectionForm(forms.Form):

    division = forms.ModelChoiceField(queryset=Division.objects.all(), label='Division', required=False, empty_label="All Divisions")


class TaskSearchForm(forms.Form):
    milestone_id = forms.CharField(required=False)
    task_id = forms.CharField(required=False)
    title = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}))
    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True).order_by('username'),
                                                label="Select Supervisor", required=False)
    task_executor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_executor=True).order_by('username'),
                                                   label="Select Executor", required=False)
    system = forms.ModelChoiceField(queryset=System.objects.all(), required=False)
    facility = forms.TypedChoiceField(choices=[("", "")], required=False)
    planned_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super(TaskSearchForm, self).__init__(*args, **kwargs)
        facility = Milestone.objects.filter(status='NotStarted').values_list('facility', flat=True).distinct()
        choice_list = []
        for each in facility:
            choice_list.append((each,each))

        self.fields['facility'].choices = choice_list
        self.fields['facility'].initial = ""

        if(kwargs.get('initial')):
            if(kwargs['initial'].get('user')):
                user = kwargs['initial']['user']

                self.fields['supervisor'].queryset = User.objects.filter(profile__is_supervisor=True,
                                                                         profile__division=user.profile.division).order_by('username')
                self.fields['task_executor'].queryset = User.objects.filter(profile__is_executor=True,
                                                                         profile__division=user.profile.division).order_by('username')

    class Meta:
        fields = ('milestone_id','task_id','title','supervisor', 'task_executor', 'system', 'facility','planned_start_date_from','planned_start_date_to','actual_start_date_from','actual_start_date_to')




class AllTaskSearchForm(forms.Form):

    milestone_id = forms.CharField(required=False)
    task_id = forms.CharField(required=False)
    title = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}))
    percent_completed = forms.IntegerField(label="Percentage Completed", required=False,max_value=100, min_value=0)
    division = forms.ModelMultipleChoiceField(queryset=Division.objects.all(), required=False)
    shop = forms.ModelMultipleChoiceField(queryset=DepartmentShop.objects.all(), required=False)
    task_category = forms.MultipleChoiceField(choices=Task.objects.all().values_list('task_category','task_category').distinct(), required=False)
    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True).order_by('username'),
                                                label="Select Supervisor", required=False)
    task_executor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_executor=True).order_by('username'),
                                                   label="Select Executor", required=False)
    system = forms.ModelChoiceField(queryset=System.objects.all(), required=False)
    subsystem = forms.ModelChoiceField(queryset=SubSystem.objects.all(), required=False)
    facility = forms.ModelChoiceField(queryset=Facility.objects.all(), required=False)
    planned_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super(AllTaskSearchForm, self).__init__(*args, **kwargs)


        if(kwargs.get('initial')):
            if(kwargs['initial'].get('user')):
                user = kwargs['initial']['user']

                div = user.profile.division
                self.fields['supervisor'].queryset = User.objects.filter(profile__is_supervisor=True,
                                                                         profile__division=div).order_by('username')
                self.fields['task_executor'].queryset = User.objects.filter(profile__is_executor=True,
                                                                         profile__division=div).order_by('username')
                sqset = None
                eqset = None
                if(user.profile.access_level<4):
                    sqset = User.objects.filter(profile__is_supervisor=True).order_by('username')
                    eqset = User.objects.filter(profile__is_executor=True).order_by('username')

                    if(len(args)>0):
                        if(args[0].get('division')):
                            div = Division.objects.get(div_id=args[0]['division'])
                            sqset = sqset.filter(profile__division=div)
                            eqset = eqset.filter(profile__division=div)
                if (user.profile.access_level >= 4):
                    self.fields['division'].queryset = Division.objects.filter(division_name=user.profile.division.division_name)
                    if(not sqset):
                        sqset = User.objects.filter(profile__division=user.profile.division)
                    else:
                        sqset = sqset.filter(profile__division=user.profile.division)

                    if(not eqset):
                        eqset = User.objects.filter(profile__division=user.profile.division)
                    else:
                        eqset = eqset.filter(profile__division=user.profile.division)

                self.fields['task_executor'].queryset = eqset
                self.fields['supervisor'].queryset = sqset

    class Meta:
        fields = ('task_id','percent_completed', 'supervisor', 'task_executor', 'system', 'facility','title','planned_start_date_from','planned_start_date_to','actual_start_date_from','actual_start_date_to')


class DocumentReqeustForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none())
    requested_documents = forms.CharField(widget=forms.Textarea(attrs={'rows':2, 'cols':40}))
    requester_remarks = forms.CharField(widget=forms.Textarea(attrs={'rows':2, 'cols':40}))


    def __init__(self, *args, **kwargs):
        super(DocumentReqeustForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            if(kwargs['initial'].get('task_id')):
                task_id = kwargs['initial']['task_id']
                task = Task.objects.filter(id=task_id)
                self.fields['task'].queryset = task
                self.fields['task'].initial = task.first()
                self.fields['requested_documents'].initial = task.first().task_id

    class Meta:
        model = DocumentRequest
        exclude = ['id', 'requested_by', 'requested_at', 'received_at', 'approved_at', 'approval_level',
                   'approved_by', 'approver_remarks', 'provided_at', 'provided_documents',
                   'provider_remarks', 'provided_by', 'provider_remarks', 'provided_at']



class DocumentReqeustApprovalForm(forms.ModelForm):
    approver_remarks = forms.CharField(widget=forms.Textarea(attrs={'rows':4, 'cols':40}),required=False)

    def __init__(self, *args, **kwargs):
        super(DocumentReqeustApprovalForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            if(kwargs['initial'].get('task_id')):
                task_id = kwargs['initial']['task_id']
    class Meta:
        model = DocumentRequest
        exclude = ['id', 'requested_by', 'requested_at', 'received_at','requested_documents','task','requester_remarks',
                    'approved_at', 'approval_level', 'approved_by', 'provided_at', 'provided_documents',
                   'provider_remarks', 'provided_by', 'provider_remarks', 'provided_at']


class DocumentProvideForm(forms.ModelForm):
    provider_remarks_choices = ["Not submitted",
                                "Partially submitted ",
                                "Delivered via storage device",
                                "Delivered via e-gov cloud",
                                "Delivered via official mail",
                                "Delivered as Hard Copy",
                                ]
    document_not_received = forms.ChoiceField(choices=[("yes", "Yes"), ("no", "No")], label="Document Available")
    provided_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'placeholder':"YYYY-mm-dd HH:MM:SS"}),required=True)
    provider_remarks = forms.CharField(required=True)
    provided_documents = forms.CharField(widget=forms.Textarea(attrs={'rows':4, 'cols':40}),required=False)

    def __init__(self, *args, **kwargs):
        super(DocumentProvideForm, self).__init__(*args, **kwargs)
        self.fields['provider_remarks'] = forms.CharField(widget=ListTextWidget(data_list=self.provider_remarks_choices,name='provider_remarks'))
    class Meta:
        model = DocumentRequest
        exclude = ['id', 'requested_by', 'requested_at', 'received_at','requested_documents','task','requester_remarks',
                    'approved_at', 'approval_level', 'approved_by', 'approver_remarks', 'provided_by',]
        fields = ['document_not_received', 'provided_documents', 'provider_remarks', 'provided_at']


class DeliveredDocumentSearchForm(forms.ModelForm):
    requested_by = forms.ModelChoiceField(queryset=User.objects.filter(id__in=DocumentRequest.objects.all().values_list('requested_by', flat=True)).order_by('username'), required=False)
    approved_by = forms.ModelChoiceField(queryset=User.objects.filter(id__in=DocumentRequest.objects.all().values_list('approved_by', flat=True)).order_by('username'), required=False)
    provided_by = forms.ModelChoiceField(queryset=User.objects.filter(id__in=DocumentRequest.objects.all().values_list('provided_by', flat=True)).order_by('username'), required=False, label='Delivered by')
    start_date = forms.DateField(label='Start date', required=False, widget=DateInput)
    end_date = forms.DateField(label='End date', required=False, widget=DateInput)

    class Meta:
        model = DocumentRequest
        fields = ['requested_by', 'approved_by','provided_by', 'start_date', 'end_date']


class PendingDocumentSearchForm(forms.Form):
    task_id = forms.CharField(label='Task ID', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50}))
    requested_by = forms.ModelChoiceField(queryset=User.objects.filter(id__in=DocumentRequest.objects.all().values_list('requested_by', flat=True)).order_by('username'), required=False)


class LectureScheduleForm(forms.ModelForm):

    target_division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False,label='Division',
                                      widget=forms.Select(attrs={"onchange": "filter_lecture_tasks_list()"}))
    task_filter = forms.CharField(label='Search keyword specific tasks',required=False)
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects.none(), required=False)
    lecture_name = forms.CharField(label='Lecture Title', widget=forms.Textarea(attrs={'rows':1, 'cols':40}), required=True)
    lecture_category = forms.CharField(label='Lecture Category', widget=forms.Textarea(attrs={'rows':2, 'cols':40}), required=False)
    lecture_description = forms.CharField(label='Description', widget=forms.Textarea(attrs={'rows': 2, 'cols': 40}),required=False)
    venue = forms.CharField(label='Venue',required=True)
    schedule = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False)
    lead_presenter = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), required=True)
    other_presenter = forms.ModelMultipleChoiceField(queryset=User.objects.all().order_by('username'), required=False, label='Other Presenters')
    other_participants = forms.ModelMultipleChoiceField(queryset=User.objects.all().order_by('username'), required=False, label='Other Participants')
    special_participants = forms.CharField(required=False)


    def __init__(self, *args, **kwargs):
        super(LectureScheduleForm,self).__init__(*args, **kwargs)
        task_qset = Task.objects.none()
        keyword = ""
        if(kwargs.get('initial')):
            task_filters = []
            if(kwargs['initial'].get('division')):
                div = kwargs['initial'].get('division')
                self.fields['target_division'].initial = div
                task_filters.append(Q(**{'division':div}))
            if(kwargs['initial'].get('keyword')):
                self.fields['task_filter'].initial = kwargs['initial'].get('keyword')
                keyword = kwargs['initial'].get('keyword').upper()
                task_filters.append(Q(**{'title__icontains':keyword}))
                task_filters.append(Q(**{'task_id__icontains': keyword}))
            date_limit = datetime.date.today()-datetime.timedelta(days=120)
            #task_filters.append(Q(**{'planned_start_date__gte':date_limit}))


            if(len(task_filters)>0):
                task_qset = Task.objects.filter(division=div,title__icontains=keyword)
                task_qset = task_qset| Task.objects.filter(task_id__icontains=keyword)
            self.fields['tasks'].queryset = task_qset.order_by('-planned_start_date')

        if(kwargs.get('instance')):
            lect_instance = kwargs['instance']
            task_list = lect_instance.tasks.all()
            self.fields['tasks'].initial = task_list
            if(task_qset):
                task_list = task_qset|task_list
            self.fields['tasks'].queryset = task_list


    class Meta:
        model = Lecture
        fields = ('target_division', 'task_filter', 'tasks', 'lecture_name', 'lecture_category',
                  'lecture_description', 'venue', 'schedule', 'lead_presenter', 'other_presenter','other_participants', 'special_participants')



class AddActualStartDateForm(forms.Form):

    add_actual_start_date = forms.DateField(label='Actual start date', required=True, widget=DateInput)

class AddActualEndDateForm(forms.Form):

    add_actual_end_date = forms.DateField(label='Actual end date', required=True, widget=DateInput)


class FeedbackSearchForm(forms.Form):
    task = forms.ModelChoiceField(queryset=Task.objects.filter(id__in=TaskFeedBack.objects.all().values_list('task__id',flat=True)), required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    task_category = forms.ChoiceField(choices=task_category, required=False)
    feedback_from = forms.DateField(widget=DateInput(attrs={'type':'date'}), required=False)
    feedback_to = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    task_from = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    task_to = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)


class TaskLeadExecutorForm(forms.ModelForm):

    lead_executor = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), required=False)
    class Meta:
        model = Task
        fields = ['lead_executor',]
        exclude = ['facility', 'system', 'subsystem', 'task_category', 'milestone_id', 'task_id', 'stage', 'title',
                   'description', 'division', 'dept_id', 'relevant_kks_codes',
                   'planned_start_date', 'planned_end_date', 'actual_end_date', 'percent_completed', 'created_date',
                   'updated_date', 'task_created_by', 'status', 'is_active','actual_start_date']

class AddTaskPercentageForm(forms.ModelForm):

    percent_completed = forms.IntegerField(label='Task Completed (%)', required=False)
    class Meta:
        model = Task
        fields = ['percent_completed',]


class OngoingTaskQuestionAnswer(ModelForm):

    answer = forms.CharField(label='Answer',widget=forms.Textarea(attrs={'rows':2, 'cols':50}),required=False)
    class Meta:
        model = QuestionsAnswers
        exclude = ('task_id','task_question','answered_by', 'created_at','is_approved')

    def __init__(self, *args, **kwargs):
        super(OngoingTaskQuestionAnswer, self).__init__(*args, **kwargs)
        if(kwargs.get('instance')):
            qa_instance = kwargs['instance']
            question = qa_instance.task_question
            answered_by = qa_instance.answered_by

            if(question.category=='MCQ'):
                choice_list = [("","Select"),(question.choice.choice_1, question.choice.choice_1),
                               (question.choice.choice_2, question.choice.choice_2)]

                self.fields['answer'] = forms.ChoiceField(choices=choice_list, label='Answer',required=False)

            if(question.category == "FILE"):
                self.fields['answer'].widget.attrs['placeholder'] = 'Will be auto filled'
                self.fields['answer'].widget.attrs['readonly'] = True
                self.fields['answer'].widget.attrs['rows'] = 1



class ConsultantTaskSearchForm(forms.Form):

    milestone_id = forms.CharField(required=False)
    task_id = forms.CharField(required=False)
    division = forms.ModelMultipleChoiceField(queryset=Division.objects.all(), required=False)
    task_category = forms.MultipleChoiceField(choices=Task.objects.all().values_list('task_category','task_category').distinct(), required=False)
    title = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}))
    system = forms.ModelChoiceField(queryset=System.objects.all(), required=False)
    facility = forms.ModelChoiceField(queryset=Facility.objects.all(), required=False)

    supervisor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True).order_by('username'),                                                label="Select Supervisor", required=False)
    task_executor = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_executor=True).order_by('username'),
                                                   label="Select Executor", required=False)
    planned_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    planned_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_start_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    actual_end_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super(ConsultantTaskSearchForm, self).__init__(*args, **kwargs)


        if(kwargs.get('initial')):
            if(kwargs['initial'].get('user')):
                user = kwargs['initial']['user']

                self.fields['supervisor'].queryset = User.objects.filter(profile__is_supervisor=True
                                                                         ).order_by('username')
                self.fields['task_executor'].queryset = User.objects.filter(profile__is_executor=True,
                                                                        ).order_by('username')

    class Meta:
        fields = ('task_id','division', 'task_category', 'title', 'system', 'facility', 'supervisor', 'task_executor' ,'planned_start_date_from','planned_start_date_to','actual_start_date_from','actual_start_date_to')

class ConsultantQAForm(forms.ModelForm):
    qa1 = forms.CharField(label='How was the quality of lead presenter?', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa2 = forms.CharField(label='How many saw programs/milestones they covered in the discussion?', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa3 = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True,profile__is_executor=True),label='Did you interact with the participants? Mention at least 3 names who performed best according to you.', required=True)
    qa4 = forms.CharField(label='Do success criteria or listed parameters or completion criteria of presented SAW program/task are adequate?', widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}), required=True)
    qa5 = forms.CharField(label='Which area of the task the specialist should concentrate most?', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa6 = forms.CharField(label='In the success criteria which criteria is the most important where variation or deviation should not be allowed by the specialist?', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa7 = forms.CharField(label='What are the key points to improve the discussions on delivered topic?', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa8 = forms.CharField(label='Number of tests is sufficient or do you have any proposal for any additional test? If yes, please mention the name of the tests.', widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), required=True)
    qa9 = forms.ModelMultipleChoiceField(queryset=User.objects.filter(profile__is_supervisor=True,profile__is_executor=True),label='Write 5 names of participants who need to improve.', required=False)
    qa10 = forms.CharField(label='Do you want to repeat the lecture?', widget=forms.Textarea(attrs={'rows': 1, 'cols': 60}), required=True)
    class Meta:
        model = ConsultantQA
        fields = ('qa1', 'qa2', 'qa3', 'qa4', 'qa5', 'qa6', 'qa7', 'qa8', 'qa9', 'qa10')

    def __init__(self,*args,**kwargs):
        super(ConsultantQAForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            lect = kwargs.get('initial').get('lecture')
            user = kwargs.get('initial').get('user')
            participants = User.objects.none()
            for each in lect.tasks.all():
                participants |= each.supervisor.all()
                participants |= each.task_executor.all()
            participants |= lect.other_participants.all()
            participants |= lect.other_presenter.all()
            participants = participants.exclude(username=user.username).order_by('username')

            self.fields['qa3'].queryset = participants.distinct()
            self.fields['qa9'].queryset = participants.distinct()

class LectureFeedbackForm(forms.ModelForm):
    qa1 = forms.CharField(label='Did you participate in the discussion?', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    qa2 = forms.CharField(label='How do you rate the consultant based on interaction with you (out of 10)?', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    qa3 = forms.CharField(label='How do you rate lead presenter on discussion (out of 10)?', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    qa4 = forms.CharField(label='Did the consultant make any value addition in the discussion? (Proper explanation/Additional information/Additional technique/Extra ordinary explanation)', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    qa5 = forms.CharField(label='Did presence of Consultant increase the quality of discussion?', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    class Meta:
        model = LectureFeedback
        fields = ('qa1', 'qa2', 'qa3', 'qa4', 'qa5')

class ConsultantTaskFeedback(forms.ModelForm):
    review_report = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 100}), required=True)
    class Meta:
        model = ConsultantTasks
        fields = ('review_report',)

class ConsultantCommentForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 6, 'cols': 60}), required=True)
    task_id = forms.ModelChoiceField(queryset=Task.objects.none(),required=False)
    def __init__(self,*args,**kwargs):
        super(ConsultantCommentForm, self).__init__(*args, **kwargs)

        if(kwargs.get('initial')):
            task_id = kwargs.get('initial').get('task_id')
            self.fields['task_id'].queryset = Task.objects.filter(id=task_id)
            self.fields['task_id'].initial = Task.objects.get(id=task_id)
    class Meta:
        model = Comment
        fields = ('task_id', 'comment')


class LectureSearchForm(forms.Form):
    target_division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, label='Division')
    lecture_name = forms.CharField(label='Title', required=False)
    lecture_category = forms.CharField(label='Category', required=False)



class LectureAddConsultant(forms.Form):
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__grade=75), required=False)

    class Meta:
        fields = ('consultant',)
class ConsultantTaskFeedbackSearchForm(forms.Form):
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__access_level=75), required=False)
    task = forms.ModelChoiceField(queryset=Task.objects.filter(id__in=ConsultantTasks.objects.filter(review_report__isnull=False).values_list('task_id')), required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    task_category = forms.ChoiceField(choices=task_category, required=False)
    feedback_from = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    feedback_to = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)


class ConsultantLectureFeedbackComment(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':4,'cols':60}))
    consultant_qa = forms.ModelChoiceField(queryset=ConsultantQA.objects.none(),label="Discussion")

    def __init__(self,*args, **kwargs):
        super(ConsultantLectureFeedbackComment, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            consultant_qa = kwargs.get('initial').get('consultant_qa')
            self.fields['consultant_qa'].queryset = ConsultantQA.objects.filter(id=consultant_qa.id)
            self.fields['consultant_qa'].initial = consultant_qa
    class Meta:
        model = Comment
        fields = ('consultant_qa','comment')

class ConsultantTaskFeedbackCommentForm(forms.ModelForm):
    consultant_task_feedback = forms.ModelChoiceField(queryset=ConsultantTasks.objects.none())
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':4,'cols':60}))
    def __init__(self,*args,**kwargs):
        super(ConsultantTaskFeedbackCommentForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            consultant_task = kwargs.get('initial').get('consultant_task')
            self.fields['consultant_task_feedback'].queryset = ConsultantTasks.objects.filter(id=consultant_task.id)
            self.fields['consultant_task_feedback'].initial = consultant_task
    class Meta:
        model = Comment
        fields = ('consultant_task_feedback','comment',)

class ConsultantLectureFeedbackSearchForm(forms.Form):
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__access_level=75), required=False)
    #task = forms.ModelChoiceField(queryset=Task.objects.filter(id__in=ConsultantTasks.objects.filter(review_report__isnull=False).values_list('task_id')), required=False)
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    lecture_category = forms.ChoiceField(choices=Task.objects.all().values_list('task_category','task_category').distinct(), required=False)
    feedback_from = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    feedback_to = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)



class ConsultancyRequestForm(forms.ModelForm):
    task = forms.ModelChoiceField(queryset=Task.objects.none())
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows':4,'cols':60}))
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__access_level=75), required=True, label="Select Consultant")
    class Meta:
        model = ConsultancyRequest
        fields = ('task','remarks','consultant')
    def __init__(self, *args, **kwargs):
        super(ConsultancyRequestForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            task = kwargs.get('initial').get('task')
            self.fields['task'].queryset = Task.objects.filter(id=task.id)
            self.fields['task'].initial = task


class ConsultancyRequestApprovalForm(forms.ModelForm):
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__access_level=75), required=False)

    class Meta:
        model = ConsultancyRequest
        fields = ('consultant',)


class ConsultancyRequestSearchForm(forms.Form):
    status = forms.ChoiceField(choices=consultancy_request_status,required=False)
    task_id = forms.CharField(required=False, label="Task")
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False)
    task_category = forms.ChoiceField(choices=Task.objects.all().values_list('task_category','task_category').distinct(), required=False)
    request_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    request_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    consultant = forms.ModelChoiceField(queryset=User.objects.filter(profile__access_level=75).order_by('username'),
                                                label="Select Consultant", required=False)

class MsgInstructionActionForm(forms.ModelForm):
    instruction = forms.ModelChoiceField(queryset=GroupMsgInstruction.objects.none(), required=False, label='Reply For')
    action_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 5,'cols': 60}))
    class Meta:
        model = MsgInstructionAction
        fields = ('instruction','action_text',)

    def __init__(self, *args, **kwargs):
        super(MsgInstructionActionForm, self).__init__(*args, **kwargs)
        if(kwargs.get('initial')):
            if(kwargs.get('initial').get('user')):
                user = kwargs.get('initial').get('user')
                if(kwargs.get('initial').get('instruction')):
                    instruction = kwargs.get('initial').get('instruction')
                    instruction_list = GroupMsgInstruction.objects.filter(recipients__contains=user.username,
                                                                          message_body=instruction.message_body).order_by('-send_time')
                    self.fields['instruction'].queryset = instruction_list


class DocumentReviewCommentsForm(forms.ModelForm):
    section_no = forms.CharField(widget=forms.Textarea(attrs={'rows':3,'cols':40}), label="Section No")
    original_text = forms.CharField(widget=forms.Textarea(attrs={'rows':3,'cols':40}), label="Original Text")
    proposed_text = forms.CharField(widget=forms.Textarea(attrs={'rows':3,'cols':40}), label="Proposed Text")
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows':3,'cols':40}), label="Remarks")

    class Meta:
        model = DocumentReviewComments
        fields = ('section_no','original_text', 'proposed_text', 'remarks')


class DocumentReviewSearchForm(forms.Form):
    task_id = forms.CharField(label='Task ID', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    title = forms.CharField(label='Title', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40, 'class':'form-control'}))
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False,widget=forms.Select(attrs={'class':'form-control'}))
    department = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(), required=False, label="Department/Shop",widget=forms.Select(attrs={'class':'form-control'}))
    user = forms.ModelMultipleChoiceField(queryset=User.objects.filter(id__in=OperationalDocumentReview.objects.all().values_list('user', flat=True)
                                                               .union(RegulationDocumentReview.objects.all().values_list('user', flat=True))
                                                               .union(FireAndEmergencyDocumentReview.objects.all().values_list('user', flat=True))
                                                               .union(OthersDocumentReview.objects.all().values_list('user', flat=True))),
                                                                required=False, label='Reviewed by')

class SecondTierReviewSearchForm(forms.Form):
    task_id = forms.CharField(label='Task ID', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    title = forms.CharField(label='Title', required=False, widget=forms.Textarea(attrs={'rows': 1, 'cols': 50, 'class':'form-control'}))
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-control'}))
    department = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(), required=False, label="Department/Shop", widget=forms.Select(attrs={'class':'form-control'}))
    committee = forms.ModelChoiceField(queryset=Committee.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-control'}))
    div_head_recommendation = forms.ChoiceField(choices=recommendation, label="Divisional Head Recommendation", required=False, widget=forms.Select(attrs={'class':'form-control'}))
    chief_engr_recommendation = forms.ChoiceField(choices=recommendation, label="Chief Engineer Recommendation", required=False, widget=forms.Select(attrs={'class':'form-control'}))
    sd_recommendation = forms.ChoiceField(choices=recommendation, label="Station Director Recommendation", required=False, widget=forms.Select(attrs={'rows': 1, 'cols': 50, 'class':'form-control'}))