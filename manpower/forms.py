import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from .models import *
from django.contrib.auth import backends, get_user_model
from django.contrib.auth.models import Group


def user_list():
    userList = list(User.objects.all().values_list('username', flat= True).order_by('username'))
    #print("userList: ", userList)
    return userList
class GroupPermissionForm(forms.Form):
    group_name = forms.CharField(widget=forms.Textarea(attrs={'size': 60, 'rows': 1}), label='Group Name',
                                 required=True)

    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']

        if (Group.objects.filter(name=group_name).count() != 0):
            raise forms.ValidationError("Group Name Already Used")
        return group_name


class UserActivationForm(forms.Form):
    user = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.CheckboxSelectMultiple)
    activation = forms.ChoiceField(choices=(("activate", "Activate"), ("deactivate", "De-activate")))

    def __init__(self, *args, **kwargs):
        super(UserActivationForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelMultipleChoiceField(queryset=User.objects.filter(is_active__in=[False]),
                                                             widget=forms.CheckboxSelectMultiple,
                                                             label="Select User(s)")
        self.fields['activation'] = forms.ChoiceField(choices=(("activate", "Activate"), ("deactivate", "De-activate")),
                                                      label="Activation Status")


class AdminResetPasswordForm(forms.Form):
    user = forms.CharField(label='Select a User')
    password = forms.CharField(label=_("New Password"),
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    confirm_password = forms.CharField(label=_("Confirm New Password"),
                                       widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, *args, **kwargs):
        super(AdminResetPasswordForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.CharField(label='Select a User',
                                              widget=ListTextWidget(data_list=user_list(), name='user'))


class UserChangePasswordForm(forms.Form):
    current_password = forms.CharField(label=_("Current Password"),
                                       widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    new_password = forms.CharField(label=_("New Password"),
                                   widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    confirm_new_password = forms.CharField(label=_("Confirm New Password"),
                                           widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


class UserGroupForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   widget=forms.Select(attrs={'onchange': "select_group_to_manage(this.id)"}),
                                   label='Select Group')
    user = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.CheckboxSelectMultiple,
                                          required=False)

    def __init__(self, *args, **kwargs):
        super(UserGroupForm, self).__init__(*args, **kwargs)
        print("UserGroup form init")

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required.  email address of rooppurnpp.gov.bd domain.')
    phone = forms.CharField(max_length=11, label='Mobile No')
    department = forms.ModelChoiceField(required=True, label="Department", queryset=DepartmentShop.objects.all())
    npcbl_designation = forms.CharField(required=False, label='NPCBL Designation')
    section = forms.ModelChoiceField(required=False, queryset=Section.objects.all())
    subsection = forms.ModelChoiceField(required=False, queryset=SubDepartment.objects.all())
    designation = forms.CharField(required=False, label="Designation")
    employee_id = forms.CharField(required=False, max_length=11, label="Employee ID")
    grade = forms.IntegerField(required=False, label="Grade")
    is_supervisor = forms.BooleanField(required=True, label= 'Supervisor')
    is_executor = forms.BooleanField(required=True, label='Executor')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email','phone', 'is_supervisor','is_executor', 'department',
                  'npcbl_designation','designation','section','subsection', 'employee_id', 'password1', 'password2')

    def clean_email(self):
        data = self.cleaned_data['email']
        if "@rooppurnpp.gov.bd" not in data:  # any check you need
            raise forms.ValidationError("Must be a rooppurnpp.gov.bd address")
        if User.objects.filter(email=data).count() != 0:
            raise forms.ValidationError(
                _("This email address is already in use. Please use a different email address."))
        return data

class DepartmentShopForm(forms.ModelForm):

    class Meta:
        model = DepartmentShop
        fields = '__all__'
        exclude = ['category_id', 'category_name', 'is_enable', 'created_date', 'updated_date','status']


class UserSearchForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    npcbl_designation = forms.CharField(required=False, label='NPCBL Designation')
    division = forms.ModelChoiceField(required=False, label="Division", queryset=Division.objects.all())
    department = forms.ModelChoiceField(required=False, label="Department", queryset=DepartmentShop.objects.all())
    subdepartment = forms.ModelChoiceField(required=False, queryset=SubDepartment.objects.all())
    section = forms.ModelChoiceField(required=False, queryset=Section.objects.all())
    phone = forms.CharField(max_length=11, required=False, label='Mobile No')
    email = forms.EmailField(max_length=254, required=False)

    def __init__(self, *args, **kwargs):
        super(UserSearchForm, self).__init__(*args, **kwargs)
        form_style = {"style": "width: 200px;"}
        self.fields["division"].widget.attrs = form_style
        self.fields["department"].widget.attrs = form_style
        self.fields["subdepartment"].widget.attrs = form_style
        self.fields["section"].widget.attrs = form_style

    class Meta:
        model = User
        fields = ('first_name', 'npcbl_designation', 'division', 'department', 'subdepartment', 'section', 'phone', 'email')


class CommitteeForm(forms.ModelForm):
    name = forms.CharField(label="Committee Name")
    division = forms.ModelChoiceField(queryset=Division.objects.all(), required=True, label="Division")
    department = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(), required=True, label="Shop/Department")
    members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label="Members", required=True)
    lead = forms.ModelChoiceField(queryset=User.objects.all(), label="Group Lead", required=True)
    div_head = forms.ModelChoiceField(queryset=User.objects.all(), label="Division Head", required=True)
    class Meta:
        model = Committee
        fields = ('name', 'division', 'department', 'members', 'lead', 'div_head')

class SARCommitteeForm(forms.ModelForm):
    name = forms.CharField(label="Committee Name", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sar_section = forms.CharField(label="Safety Analysis Report Section", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sar_section_title = forms.CharField(label="Safety Analysis Report Section Title", widget=forms.TextInput(attrs={'class': 'form-control'}))
    members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label='Committee Members')
    lead = forms.ModelChoiceField(queryset = User.objects.all(), label="Group Lead")
    class Meta:
        model = SafetyAnalysisReportCommittee
        fields = ('name', 'sar_section', 'sar_section_title', 'members', 'lead')