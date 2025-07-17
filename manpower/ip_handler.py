import csv
from io import StringIO

from django.shortcuts import render, redirect
from datetime import datetime,timedelta
import random, string
from django.shortcuts import render, redirect
from django.http import  HttpResponse, HttpResponseForbidden
from manpower.models import IPWhitelist

from operational_management_system.settings import PYTZ_TIME_ZONE
from system_log.models import *

from csv import reader


def ip_request_handler(request,action=""):
    if(action == "upload"):
        return add_ip_filter(request)
    else:
        return HttpResponse("NOT ALLOWED")

def add_ip_filter(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))

        ip_list = []
        for row in reader:
            try:
                ip_subnet = row[0].strip()
                ip = ip_subnet.split('/')[0]
                subnet = ip_subnet.split('/')[1]
                country = row[1].strip()
                c_code = row[2].strip()
                new_ip = IPWhitelist(ip_address=ip, subnet=subnet, version="4", country_code=c_code)
                ip_list.append(new_ip)

                if(len(ip_list)==10):
                    IPWhitelist.objects.bulk_create(ip_list,batch_size=10,ignore_conflicts=True)
                    ip_list = []

            except Exception as e:
                print("Error: ",e.__str__())
        if (len(ip_list) > 0):
            IPWhitelist.objects.bulk_create(ip_list, ignore_conflicts=True)

    return HttpResponse("OK")