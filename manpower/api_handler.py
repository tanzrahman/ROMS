import datetime
from datetime import timezone
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from manpower.models import DepartmentShop, User
from django.shortcuts import render, redirect
from manpower.forms import DepartmentShopForm
from task_management.models import System, SubSystem, Facility
from django.http import HttpResponse, JsonResponse
import csv
from io import StringIO


def handle_api_request(request,action):
    if(action == 'facility'):
        return add_facilities(request)
    if (action == 'tasks'):
        return add_tasks(request)
    if (action == 'system'):
        return add_systems(request)


def add_systems(request):
    sub_system = {
        "CPS-ESFAS": ["EP-ESFAS IP", "DPS(IP, AP)", "NFME", "EP AP", "PP IP", "GICS", "ARPC", "PP AP", "IDN CAS"
                      , "PC CAS", "LP CAS", "SS V CAS", "MCR V CAS", "ECR V CAS", "PAMS CAS", "ISPS"]

        , "MCDS": ["ICIS", "ALMS", "HLMS", "VMS", "LMS", "LPDS", "ARLMS"]

        , "LDS-2": ["LDS-2"]

        , "NO I&C": ["RC I&C CAS", "TC I&C CAS", "AWT I&C CAS", "CWT I&C CAS", "V I&C CAS"]

        , "ULCS": ["ULCS", "RVD"]

        , "SLCS": ["SLCS"]

        , "ARMS": ["ARMS"]

        , "IOPRS": ["IOPRS"]

        , "FP I&C": ["FP I&C"]

        , "AVMDS": ["AVMDS"]

        , "MCR/ECR panels and consoles": ["SS panels", "NO panels"]

        , "MCR SS": ["D V I&C", "PSEL I&C CAS"]

        , "NO LCP": ["UPS I&C CAS", "Cooling tower I&C CAS", "V LAN I&C CAS"]

        , "LCPrel": ["LCPrel"]

        , "EE I&C": ["PU EE I&C", "CS A EE I&C"]

        , "TGEP/TPEP": ["TGEP", "TPEP"]

        , "HSAME": ["HSAME"]

        , "WC I&C": ["WC I&C"]
        ,  "PHRS CC": ["PHRS CC"]
        , "CP LCP I&C": ["CP LCP I&C"]
        , "HCME": ["HCME"]
        , "Radiation monitoring sampling probe": ["Radiation monitoring sampling probe"]
        , "RAW I&C": ["RAW I&C"]
        , "RVLIS": ["RVLIS"]
        ,"ICDA": ["ICDA"]
    }

    system = ["CPS-ESFAS", "MCDS", "LDS-2", "FP I&C", "AVMDS", "MCR SS", "NO LCP", "RAW I&C",
              "NO I&C", "ULCS", "SLCS", "ARMS","IOPRS", "MCR/ECR panels and consoles", "LCPrel",
              "EE I&C", "TGEP/TPEP", "TGEP/TPEP", "HSAME", "WC I&C", "PHRS CC", "CP LCP I&C", "HCME",
              "Radiation monitoring sampling probe","RVLIS", "ICDA"]

    for each in system:
        each_upper = each.upper()
        if(System.objects.filter(name=each_upper).count()<1):
            new_system = System(name=each_upper,code=each_upper)
            new_system.save()

    for each in system:
        each_upper = each.upper()
        system = System.objects.get(name=each_upper)

        sub_systems = sub_system[each]
        for subsys in sub_systems:
            subsys = subsys.upper()
            if(SubSystem.objects.filter(name=subsys).count()<1):
                new_system = SubSystem(name=subsys, system=system)
                new_system.save()
    return HttpResponse("SYSTEMS, SubSystems ADDED")


def add_facilities(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        for row in reader:
            kks = row[0]
            name = row[1]
            if(Facility.objects.filter(kks_code=kks).exists()):
                continue
            else:
                new_fac = Facility(name=name, kks_code=kks)
                new_fac.save()

        return HttpResponse('Facilities added')

def add_tasks(request):
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        # for row in reader:
        #     kks = row[0]
        #     name = row[1]
        #     if(Facility.objects.filter(kks_code=kks).exists()):
        #         continue
        #     else:
        #         new_fac = Facility(name=name, kks_code=kks)
        #         new_fac.save()

        return HttpResponse('Tasks added')

@csrf_exempt
def user_login_api(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            response = JsonResponse({"message": "Login successful"})
            response.set_cookie("sessionid", request.session.session_key)
            return response
        else:
            return JsonResponse({"message": "Invalid credentials"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)