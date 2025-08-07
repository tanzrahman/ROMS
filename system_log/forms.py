from task_management.models import Task, User
from manpower.models import Profile, Division, DepartmentShop
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from functools import reduce
import operator
from django.contrib.auth import backends, get_user_model
from django.contrib.auth.models import Group

designation_choices = [
    ("all", "All Person of the Division"), ("div_head", "Division Head"), ("shop_man", "Shop Manager"),
    ("dep_shop_man", "Deputy Shop Manager"), ("job_dist", "Job Distributor"),
    ("supervisor", "Supervisor"), ("executor", "Executor")]


class GroupSMSForm(forms.Form):
    tasks = forms.ModelMultipleChoiceField(queryset=Task.objects.filter(task_category='SAW').order_by('-id'), required=False)
    receiver_division = forms.ModelMultipleChoiceField(queryset=Division.objects.all(), required=False)
    receiver_designation = forms.MultipleChoiceField(choices=designation_choices, required=False)
    department = forms.ModelMultipleChoiceField(queryset=DepartmentShop.objects.all(), required=False)
    user = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False, label='User(s)')
    msg_body = forms.CharField(widget=forms.Textarea(), max_length=160, required=True)

    def __init__(self, *args, **kwargs):
        super(GroupSMSForm, self).__init__(*args, **kwargs)
        self.fields['tasks'].queryset = Task.objects.filter(task_category='SAW').order_by('-id')
        self.fields['user'].queryset = User.objects.all()