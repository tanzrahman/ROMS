import datetime
import threading
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.forms import *
import csv
from io import StringIO
from task_management.notify_users import send_reassign_notification, send_consultant_task_notification
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from technical_solution.models import *
from technical_solution.forms import *


def ts_list(request):
    page_no = 1
    if (request.GET.get('page_no')):
        page_no = int(request.GET.get('page_no'))

    no_of_items = 100

    search_form = TSSearchForm()
    filters = []
    if (request.GET):
        search_form = TSSearchForm(request.GET)
        if (search_form.is_valid()):
            for each in search_form.changed_data:
                if ('date' in each):
                    if ('date_from' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('date_to' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                if ('deadline' in each):
                    if ('from' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__gte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                    if ('to' in each):
                        field_name = each.rsplit('_', 1)[0]
                        date_filter = field_name + "__lte"
                        filters.append(Q(**{date_filter: search_form.cleaned_data[each]}))
                        continue
                if ('sr_no' in each):
                    filters.append(Q(**{'sr_no__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('title' in each):
                    filters.append(Q(**{'title__icontains': search_form.cleaned_data[each].upper()}))
                    continue
                if ('division' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue
                if ('shop' in each):
                    filters.append(Q(**{each + '__in': search_form.cleaned_data[each]}))
                    continue

                else:
                    print(each)
                    filters.append(Q(**{each + '__icontains': search_form.cleaned_data[each].upper()}))

    if (len(filters) > 0):
        ts_list = TechnicalSolution.objects.filter(reduce(operator.and_, filters))
        total_ts = ts_list.count()

    else:
        ts_list = TechnicalSolution.objects.all()
        total_ts = ts_list.count()

    paginator = Paginator(ts_list, no_of_items)

    try:
        ts_list = paginator.page(page_no)

    except PageNotAnInteger:
        ts_list = paginator.page(page_no)

    except EmptyPage:
        ts_list = paginator.page(paginator.num_pages)


    context = {
        'ts_list': ts_list,
        'total_ts': total_ts,
        'form': search_form
    }

    return render(request, 'technical_solution/all_ts_list.html', context=context)