import datetime
from datetime import timezone
from manpower.models import DepartmentShop, User
from django.shortcuts import render, redirect
from manpower.forms import DepartmentShopForm
from task_management.models import System, SubSystem
from django.http import HttpResponse
def department_request(request,action=None,id=None):
    if(request.user.is_anonymous):
        return redirect('/')
    
    if(not action ):
        department_list = DepartmentShop.objects.all()
        return render(request,'manpower/department.html',{'department_list':department_list})

    if(action == 'create'):
        return create_department(request)
    if (action == 'edit'):
        return edit_department(request, id)
    if (action == 'delete'):
        return delete_department(request, id)

    if(action == 'add_system'):
        return add_systems(request)



def add_systems(request):
    sub_system = ["EP-ESFAS IP", "DPS(IP, AP)", "NFME", "EP AP", "PP IP", "GICS", "ARPC", "PP AP", "IDN CAS"
        , "PC CAS", "LP CAS", "SS V CAS", "MCR V CAS", "ECR V CAS", "PAMS CAS", "ISPS", "ICIS", "ALMS"
        , "HLMS", "VMS", "LMS", "LPDS", "ARLMS", "LDS-2", "RC I&C CAS", "TC I&C CAS", "AWT I&C CAS"
        , "CWT I&C CAS", "V I&C CAS", "ULCS", "RVD", "SLCS", "ARMS", "IOPRS", "FP I&C", "AVMDS", "SS panels"
        , "NO panels", "D V I&C", "PSEL I&C CAS", "UPS I&C CAS", "Cooling tower I&C CAS", "V LAN I&C CAS"
        , "LCPrel", "PU EE I&C", "CS A EE I&C", "TGEP", "TPEP", "HSAME", "WC I&C", "PHRS CC", "CP LCP I&C", "HCME"
        , "Radiation monitoring sampling probe", "RAW I&C"]

    system = ["CPS-ESFAS", "MCDS", "LDS-2", "FP I&C", "AVMDS", "MCR SS", "NO LCP", "RAW I&C",
              "NO I&C", "ULCS", "SLCS", "ARMS","IOPRS", "MCR/ECR panels and consoles", "LCPrel",
              "EE I&C", "TGEP/TPEP", "TGEP/TPEP", "HSAME", "WC I&C", "PHRS CC", "CP LCP I&C", "HCME",
              "Radiation monitoring sampling probe"]

    for each in system:
        new_system = System(name=each,code=each)
        new_system.save()

    for each in sub_system:
        new_system = SubSystem(name=each,code=each)
        new_system.save()
    return HttpResponse("SYSTEMS, SubSystems ADDED")

def create_department(request):
    if (request.method == 'GET'):
        form = DepartmentShopForm()
        return render(request, 'manpower/department.html', {'form': form})
    if (request.method == 'POST'):
        form = DepartmentShopForm(request.POST)
        context ={}
        if (form.is_valid()):
            department = form.save(commit=False)
            department.created_at = datetime.date.today()
            department.is_enable = True
            department.status = 1
            department.save()
            form = DepartmentShopForm()
            context.update({'form': form})
            context.update({'success':'success'})
        return render(request, 'manpower/department.html', context)

def edit_department(request,dept_id):
    dept = DepartmentShop.objects.get(dept_id=dept_id)
    if (request.method == 'GET'):
        form = DepartmentShopForm(instance=dept)
        return render(request, 'manpower/department.html', {'form': form})
    if (request.method == 'POST'):
        form = DepartmentShopForm(request.POST,instance=dept)
        context = {}
        if (form.is_valid()):
            department = form.save(commit=False)
            department.updated_at = datetime.date.today()
            department.save()
            form = DepartmentShopForm()
            context.update({'form': form})
            context.update({'success':'success'})
        return render(request, 'manpower/department.html', {'form': form})


def delete_department(request, dept_id):
    dept = DepartmentShop.objects.get(dept_id=dept_id)
    dept.delete()
    return redirect('/manpower/department')
