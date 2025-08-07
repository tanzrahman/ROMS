import datetime
import re
from dis import Instruction

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from manpower.fields import ListTextWidget
from technical_solution.models import *
from .models import *
from django.db.models import Q
from functools import reduce
import operator
from django.contrib.auth import backends, get_user_model
from django.contrib.auth.models import Group


class TSSearchForm(forms.Form):
    sr_no = forms.CharField(required=False)
    ts_doc_code = forms.CharField(required=False)
    title = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':1, 'cols':40}))

    ase_ref_letter = forms.CharField(required=False)
    ase_ref_letter_date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="From")
    ase_ref_letter_date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="To")
    description = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':1, 'cols':40}))
    division = forms.ModelChoiceField(queryset=Division.objects.all(),required=False)
    shop = forms.ModelChoiceField(queryset=DepartmentShop.objects.all(),required=False)
    facility_kks = forms.CharField(required=False)
    relevant_wd_code = forms.CharField(required=False)
    reason_for_ts = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':1, 'cols':40}))
    modification_type = forms.CharField(required=False)
    deadline_for_temporary_solution_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="From")
    deadline_for_temporary_solution_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="To")

    class Meta:
        fields = "__all__"