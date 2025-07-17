import csv
import operator
from functools import reduce
from io import StringIO

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import JsonResponse, FileResponse, HttpResponse
from task_management.models import File, SystemParameter, SubSystem, Facility
from django.shortcuts import render, redirect
from datetime import datetime,timedelta
from django.contrib.auth.forms import UserCreationForm
import random, string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, GroupManager, Permission
from django.http import  HttpResponse, HttpResponseForbidden
from manpower.models import User, Profile, SubDepartment, DepartmentShop, Section, Division, Committee, SafetyAnalysisReportCommittee, \
    UserConsentDocReviewRemarks, ApprovalSignature
from .forms import GroupPermissionForm, UserActivationForm, AdminResetPasswordForm, UserChangePasswordForm, SignUpForm, \
    UserSearchForm, CommitteeForm, SARCommitteeForm
from operational_management_system.settings import PYTZ_TIME_ZONE
from system_log.models import UserLog, UserNotificationLog, UserDeactivateLog, FailedLoginLog, PasswordChangeLog
from task_management.ftp_handler import upload_to_ftp, FILETYPE, fetch_file
from csv import reader

def request_handler(request, action=None, query_string=None):
    if (action == 'embedd_signature'):
        return embedd_signature(request, query_string)

    if (request.user.is_anonymous):
        return redirect('/')

    if (not action):
        return render(request, 'manpower/user_base.html')

    if(action == 'profile'):
        return user_profile(request, query_string)
    if (action == 'change_password'):
        return change_password(request, query_string)
    if(action == 'upload_signature'):
        return upload_signature(request, query_string)
    if(action == 'load_signature'):
        return load_signature(request, query_string)
    if(action == 'committee'):
        return committee_list(request, query_string)
    if (action == 'sar_committee'):
        return sar_committee_list(request, query_string)
    if (action == 'create_committee'):
        return create_committee(request)
    if (action == 'create_sar_committee'):
        return create_sar_committee(request)
    if (action == 'edit_sar_committeee'):
        return edit_sar_committee(request,query_string)
    if(action == 'user_consent'):
        return doc_review_consent(request,query_string)
    if(action == 'consent_correction'):
        return consent_correction(request)
    if (action == 'all'):

        filters = []
        search_form = UserSearchForm()
        context = {'form': search_form}
        if (request.GET):
            search_form = UserSearchForm(request.GET)
            if (search_form.is_valid()):

                for each in search_form.changed_data:

                    if ('first_name' in each):
                        filters.append(Q(**{'first_name__icontains': search_form.cleaned_data[each].upper()}))
                        continue
                    if ('npcbl_designation' in each):
                        filters.append(Q(**{'profile__npcbl_designation__icontains': search_form.cleaned_data[each].upper()}))
                        continue
                    if ('designation' in each):
                        filters.append(Q(**{'profile__designation__icontains': search_form.cleaned_data[each].upper()}))
                        continue
                    if ('email' in each):
                        filters.append(Q(**{'email__icontains': search_form.cleaned_data[each].upper()}))
                        continue
                    if ('division' in each):
                        filters.append(Q(**{'profile__'+each: search_form.cleaned_data[each]}))
                        continue
                    else:
                        filters.append(Q(**{'profile__'+each: search_form.cleaned_data[each]}))

        if (len(filters) > 0):
            users = User.objects.filter(reduce(operator.and_, filters))
            context.update({'users': users, 'user_count': users.count()})
        else:
            users = User.objects.all().order_by('profile__grade')
            context.update({'users': users, 'user_count': users.count()})

        page_no = 1
        if (request.GET.get('page_no')):
            page_no = int(request.GET.get('page_no'))

        no_of_items = 100
        if (request.user.profile.access_level > 3):
            users = users.filter(profile__division=request.user.profile.division)

        paginator = Paginator(users, no_of_items)

        try:
            users = paginator.page(page_no)

        except PageNotAnInteger:
            users = paginator.page(page_no)

        except EmptyPage:
            users = paginator.page(paginator.num_pages)


        context.update({'users': users})
        if(request.user.profile.grade):
            if(request.user.profile.grade < 2):
                context.update({
                    'can_view_designation':True
                })

        return render(request, 'manpower/all_users.html', context)

    if (not request.user.has_perm("auth.change_user")):
        return HttpResponse("UnAuthorized Access", 401)

    if (action == "signup" or action =='create'):
        return signup(request)
    if(action == 'user_activation'):
        return user_activation(request,query_string)
    if (action == 'reset_pass'):
        return reset_password(request, query_string)



def user_profile(request,query_string):
    if(request.user.is_anonymous):
        return redirect('/login')
    else:
        user = request.user
        user = User.objects.get(username=user)
        return render(request,'user.html',{'user':user})


def signup(request):
    if (request.method == "GET"):
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})
    else:
        user_form = SignUpForm(request.POST)
        if (user_form.is_valid()):
            # send an email token for the user to confirm account
            user = user_form.save()

            user.profile.email_validation_token = random_string_using_bias(user.email)
            user.profile.validation_expire_date_time = datetime.now() + timedelta(hours=12)
            user.profile.employee_id = user_form.cleaned_data['employee_id']
            user.is_active=False
            user.profile.department = user_form.cleaned_data['department']
            user.save()
            form = SignUpForm()
            return render(request, 'signup.html', {'form': form, "submission_success": "success"})
        else:
            return render(request, 'signup.html', {'form': user_form})


def random_string_using_bias(user_email):
    email_user_name = user_email.split('@')[0]
    random_string = ""
    special = "!$%&*?@#"
    string_range = special + string.ascii_letters + string.digits
    for i in range(len(email_user_name)):
        random_string = random_string+ random.choice(string_range)
    return random_string

def user_activation(request,query_string):
    if (request.method == 'GET'):
        form = UserActivationForm()
        return render(request, 'user_activation.html', {'form': form})
    else:
        form = UserActivationForm(request.POST)
        if(form.is_valid()):
            for user_obj in form.cleaned_data['user']:
                user_obj.is_active = True
                user_obj.save()
            result = "success"
            return render(request, 'user_activation.html', {'form': form, "result":result})
        else:
            return render(request, 'user_activation.html', {'form': form})

def reset_password(request, query_string):
    if (request.method == 'GET'):
        form = AdminResetPasswordForm()
        return render(request, 'reset_password.html', {'form': form})

    else:
        form = AdminResetPasswordForm(request.POST)

        if(form.is_valid()):
            username = request.POST['user']
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']

            user = User.objects.get(username= username)

            if (password == confirm_password):
                user.set_password(password)
                user.is_active = True
                user.save()
                result = "success"
                return render(request, 'manpower/reset_password.html', {'form': form, "result": result})
            else:
                result = "Password and Confirm Password are not same"
                return render(request, 'manpower/reset_password.html', {'form': form, "result": result})
        else:
                return render(request, 'manpower/reset_password.html', {'form': form})


def change_password(request, query_string):
    if (request.method == 'GET'):
        form = UserChangePasswordForm()
        return render(request, 'manpower/user_change_password.html', {'form': form})

    else:
        form = UserChangePasswordForm(request.POST)

        if(form.is_valid()):
            username = request.user.username
            password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_new_password']

            user = User.objects.get(username= username)

            if (password == confirm_password):
                user.set_password(password)
                user.is_active = True
                user.save()

                # Save password change information to PasswordChange Log
                change_password = PasswordChangeLog(user_id=username, time=datetime.now(),
                                              ip=request.META['REMOTE_ADDR'])
                change_password.save()
                result = "success"
                return render(request, 'manpower/user_change_password.html', {'form': form, "result": result})
            else:
                result = "Password and Confirm Password are not same"
                return render(request, 'manpower/user_change_password.html', {'form': form, "result": result})
        else:
                return render(request, 'manpower/user_change_password.html', {'form': form})

def user_login(request):
    if (request.method == 'GET'):
        if (request.user.is_anonymous):
            return render(request, 'login.html')
        else:
            username = request.user
            return redirect('/')
    else:
        user_name = request.POST['username']
        password = request.POST['password']

        # checking username from User
        if (User.objects.filter(username=user_name).count()!=0):
            # checking user in failed login log
            login_failed = FailedLoginLog.objects.filter(user_id=user_name).first()
            print("login:", login_failed)

            #user = User.objects.get(username=user_name)

            # No of allowable login attempt value comes from system parameter table
            login_attempt_object = SystemParameter.objects.filter(name='login_attempt')
            attempt_count = 5
            if (login_attempt_object.count() != 0):
                attempt_count = login_attempt_object[0].value

            if(login_failed == None):
                logged_in_user = authenticate(username=user_name, password=password)

                if (logged_in_user):
                    login(request, logged_in_user)

                    # delete user details from failed login log
                    user = FailedLoginLog.objects.filter(user_id=user_name)
                    if (user.count() != 0):
                        user.delete()

                    # insert user access details to userlog
                    user_access_details = UserLog(user_id=user_name, time=datetime.now(),
                                                  ip=request.META['REMOTE_ADDR'])
                    user_access_details.save()
                    request.session.set_expiry(6*3600)

                    # if(logged_in_user.profile.grade > 25):
                    #     return redirect('/task_list_ru')
                    return redirect('/')

                else:
                    # insert failed login details to failed login log table
                    failed_login = FailedLoginLog(user_id=user_name, time=datetime.now(),
                                                  ip=request.META['REMOTE_ADDR'], login_attempt_count=1)
                    failed_login.save()
                    return render(request, 'login.html', {"error": "failed_login"})

            else:
                if (login_failed.login_attempt_count < attempt_count):
                    logged_in_user = authenticate(username=user_name, password=password)

                    if (logged_in_user):
                        login(request, logged_in_user)

                        # delete user details from failed login log
                        user = FailedLoginLog.objects.filter(user_id=user_name)
                        if (user.count() != 0):
                            user.delete()
                        # insert user access details to userlog
                        user_access_details = UserLog(user_id=user_name, time=datetime.now(),
                                                      ip=request.META['REMOTE_ADDR'])
                        user_access_details.save()
                        return redirect('/')

                    else:
                        # update login attempt count by 1 and assigned last ip to ip address field
                        login_failed.login_attempt_count += 1
                        login_failed.ip = request.META['REMOTE_ADDR']
                        login_failed.save()
                        return render(request, 'login.html', {"error": "failed_login"})
                else:
                    user = User.objects.get(username=user_name)
                    user.is_active = False
                    user.save()

                    # assign login attempt count to 0 in Failed Login Log
                    login_failed.login_attempt_count = 0
                    login_failed.save()

                    # insert deactivate user list in user_deactivate log
                    deactivate_user_details = UserDeactivateLog(user_id=str(user_name),
                                                                    time=datetime.now(tz=PYTZ_TIME_ZONE),
                                                                    ip=request.META['REMOTE_ADDR'], deactivation_details= "Exceeded login attempt")
                    deactivate_user_details.save()

                    return render(request, "429.html", status=429)

        else:
            return render(request, 'login.html',{"error":"failed_login"})


def logout_user(request):
    logout(request)
    return redirect('/login/')


def add_user_from_file(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if(request.method == 'GET'):
        return render (request,'manpower/add_user_from_file.html')

    if(request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        password = 'vver1200@RNPP'
        reader = csv.reader(StringIO(file.decode('utf-8')))

        for row in reader:
            try:
                name = row[0].strip()
                designation = row[1].strip()
                section = row[2].strip()
                sub_dept = row[3].strip()
                shop = row[4].strip()
                division = row[5].strip()
                npcbl_desg = row[6].strip()
                discipline = row[7].strip()
                grade = int(row[8].strip())
                mobile = "0"+row[9].strip()
                email = row[10].lower().strip().replace(' ','')
                joining_date = row[11]
                name_parts = name.split(' ')
                length = len(name_parts)
                last_name = name_parts[length - 1]
                first_name = ""

                if(User.objects.filter(email=email).count()>0):
                    print(email, "Already Exists ")
                    continue

                # if (not 'rooppurnpp' in email):
                #     continue
                # if (designation == ""):
                #     continue
                # if (shop == "" and grade > 3):
                #     continue

                if(length > 1):
                    for i in range(0,length-1):
                        first_name = first_name + name_parts[i] + ' '
                else:
                    first_name = name
                    last_name = ""

                if(Division.objects.filter(division_name=division).count()<1):
                    new_div = Division(division_name=division)
                    new_div.save()

                if(SubDepartment.objects.filter(subdepartment_name=sub_dept).count()<1):
                    new_subd = SubDepartment(subdepartment_name=sub_dept)
                    new_subd.save()

                if(DepartmentShop.objects.filter(dept_name=shop).count()<1):
                    new_shop = DepartmentShop(dept_name=shop)
                    new_shop.save()
                if(Section.objects.filter(section_name=section).count()<1):
                    new_section = Section(section_name=section)
                    new_section.save()

                if(not 'rooppurnpp' in email):
                    print("{}, {}, {}, does not have official email".format(name, designation, mobile))
                new_user = User.objects.create_user(username=email.lower(), email=email.lower(), password=password)
                new_user.is_active = True
                new_user.save()
                new_user.first_name = first_name
                new_user.last_name = last_name
                new_user.profile.phone = mobile
                new_user.profile.designation = designation
                new_user.profile.npcbl_designation = npcbl_desg
                new_user.profile.division = Division.objects.get(division_name=division)
                new_user.profile.department = DepartmentShop.objects.get(dept_name=shop)
                new_user.profile.section = Section.objects.get(section_name=section)
                new_user.profile.subdepartment = SubDepartment.objects.get(subdepartment_name=sub_dept)
                new_user.profile.grade = grade
                new_user.profile.is_executor = False
                new_user.profile.is_supervisor = False
                new_user.profile.access_level = grade

                if(grade <=6):
                    new_user.profile.is_supervisor = True
                if(grade >= 7):
                    new_user.profile.is_executor = True
                new_user.save()
            except Exception as e:
                print(row, e)

        return render(request, 'manpower/add_user_from_file.html')



def add_simple_user(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if(request.method == 'GET'):
        return render (request,'manpower/add_user_from_file.html')

    if(request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        password = 'vver1200@RNPP'
        reader = csv.reader(StringIO(file.decode('utf-8')))

        division = None
        count = 0
        for row in reader:
            if(count ==0):
                count +=1
                continue
            count +=1
            try:
                name = row[1].strip()

                email = row[0].lower().strip().replace(' ','')
                mobile = row[2].strip()
                division_name = row[3].strip()

                name_parts = name.split(' ')
                length = len(name_parts)
                last_name = name_parts[length - 1]
                first_name = ""
                if (length > 1):
                    for i in range(0, length - 1):
                        first_name = first_name + name_parts[i] + ' '
                else:
                    first_name = name
                    last_name = ""

                if(User.objects.filter(email=email).count()>0):
                    continue

                if(not division):
                    division = Division.objects.get(division_name=division_name)
                new_user = User.objects.create_user(username=email.lower(), email=email.lower(), password=password)
                new_user.is_active = True
                new_user.save()
                new_user.first_name = first_name
                new_user.last_name = last_name
                new_user.profile.phone = "0"+mobile
                new_user.profile.access_level = 9
                new_user.profile.grade = 9
                new_user.profile.is_executor = True
                new_user.profile.is_supervisor = False
                new_user.profile.division = division

                new_user.save()

            except Exception as e:
                print(row, e)

        return render(request, 'manpower/add_user_from_file.html')


def user_existance_checker(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        failed = open("failed.txt", "w")
        new_user = open("new_user.txt", "w")

        count = 0
        new_email = {}
        curr_date = datetime.today()
        print(curr_date)
        for row in reader:
            if count == 0:
                print(row)
                count += 1
                continue
            count += 1
            print(count)
            try:
                master_page_id = row[0].strip()
                milestone_id = row[1].strip()
                supervisor_1_phone = row[7].strip()
                supervisor_1_email = row[8].strip().replace(' ', '').lower()

                supervisor_2_phone = row[9].strip()
                supervisor_2_email = row[10].strip().replace(' ', '')

                executor_1_phone = row[11].strip()
                executor_1_email = row[12].strip().replace(' ', '').lower()

                executor_2_phone = row[13].strip()
                executor_2_email = row[14].strip().replace(' ', '').lower()
                facility_kks = row[0].strip()

                if(Facility.objects.filter(kks_code=facility_kks).count()<1):
                    Facility.objects.create(kks_code=facility_kks)

                facilty_obj = None
                milestone_obj = None

                if(User.objects.filter(email=executor_1_email).count()<1):
                    if(not new_email.get(executor_1_email)):
                        new_user.write(executor_1_email+","+executor_1_phone+"\n")
                        new_email[executor_1_email] = True
                if (User.objects.filter(email=executor_2_email).count() < 1):
                    if (not new_email.get(executor_2_email)):
                        new_user.write(executor_2_email+","+executor_2_phone+"\n")
                        new_email[executor_2_email] = True

                if (User.objects.filter(email=supervisor_1_email).count() < 1):
                    if (not new_email.get(supervisor_1_email)):
                        new_user.write(supervisor_1_email + "," + supervisor_1_phone + "\n")
                        new_email[supervisor_1_email] = True
                if (User.objects.filter(email=supervisor_2_email).count() < 1):
                    if (not new_email.get(supervisor_2_email)):
                        new_user.write(supervisor_2_email + "," + supervisor_2_phone + "\n")
                        new_email[supervisor_2_email] = True

            except Exception as e:
                msg = "Failed, {}, {}".format(milestone_id, e.__str__())
                failed.write(msg)
        failed.close()
        new_user.close()
        return HttpResponse("Task Assignment Done")


def upload_signature(request, query_string):

    if(request.method == 'POST'):
        signature = request.FILES['signature']
        sig_hash = request.POST.get('signature_hash')
        sig_file_name = str(request.user.id)+"_"+signature.name
        try:
            server_url = upload_to_ftp(signature.file, sig_file_name)
            File.objects.create(file_name=sig_file_name, hash=sig_hash, server_loc=server_url, file_size=signature.size)
            request.user.profile.signature = sig_hash
            request.user.profile.save()
            return redirect("/manpower/user/profile")
        except Exception as e:
            return HttpResponse("Failed, {}".format(e.__str__()))


    return render(request, 'manpower/upload_signature.html')

def load_signature(request, query_string):
    hash = request.GET.get('hash')
    if (request.user.profile.signature != hash):
        return HttpResponse("")

    file_object = File.objects.get(hash=hash)
    file = fetch_file(request, file_object.server_loc)
    ftype = file_object.file_type.lower()
    response = HttpResponse(file, content_type=FILETYPE[ftype])
    response['Content-Disposition'] = 'inline; filename="' + file_object.file_name + '"'
    return response

def embedd_signature(request, query_string):
    hash = request.GET.get('hash')

    file_object = File.objects.get(hash=hash)
    file = fetch_file(request, file_object.server_loc)
    ftype = file_object.file_type.lower()
    response = HttpResponse(file, content_type=FILETYPE[ftype])
    response['Content-Disposition'] = 'inline; filename="' + file_object.file_name + '"'
    return response

def committee_list(request, query_string):
    if(request.user.is_anonymous):
        return redirect('/login')
    else:
        list = Committee.objects.all()
        context = {'committee': list}
        return render(request,'manpower/committee.html', context)


def create_committee(request):
    if(request.user.is_anonymous):
        return redirect('/login')
    else:
        form = CommitteeForm()
        context = {'form': form}

        if(request.method == 'POST'):
            form = CommitteeForm(request.POST)
            if(form.is_valid()):
                cmt = form.save()
                form = CommitteeForm()
                context.update({'success': 'success', 'form': form})
            else:
                context = {'form': form}
        return render(request,'manpower/create_committee.html', context)


def create_sar_committee(request):
    if(request.user.is_anonymous):
        return redirect('/login')
    else:
        form = SARCommitteeForm()
        context = {'form': form}

        if(request.method == 'POST'):
            form = SARCommitteeForm(request.POST)
            if(form.is_valid()):
                cmt = form.save()
                form = SARCommitteeForm()
                lead = cmt.lead
                if(lead not in cmt.members.all()):
                    cmt.members.add(lead)
                perm = Permission.objects.get(codename='add_safetyanalysisreportreview')
                if(not lead.has_perm(perm)):
                    lead.user_permissions.add(perm)
                cmt.save()
                context.update({'success': 'success', 'form': form})
            else:
                context = {'form': form}
        return render(request,'manpower/create_committee.html', context)

def sar_committee_list(request, query_string):
    list = SafetyAnalysisReportCommittee.objects.all()
    context = {'sar_committee': list}
    return render(request,'manpower/committee.html', context)

def edit_sar_committee(request,query_string):
    sar_committee = SafetyAnalysisReportCommittee.objects.get(id=int(query_string))
    form = SARCommitteeForm(instance=sar_committee)
    context = {'form': form}

    if (request.method == 'POST'):
        form = SARCommitteeForm(request.POST,instance=sar_committee)
        if (form.is_valid()):
            cmt = form.save()
            form = SARCommitteeForm()
            lead = cmt.lead
            if (lead not in cmt.members.all()):
                cmt.members.add(lead)
            perm = Permission.objects.get(codename='add_safetyanalysisreportreview')
            if (not lead.has_perm(perm)):
                lead.user_permissions.add(perm)
            cmt.save()
            context.update({'success': 'success', 'form': form})
        else:
            context = {'form': form}
    return render(request, 'manpower/create_committee.html', context)

def doc_review_consent(request,query_string):

    msg = ("As per the decision made by the higher officials of Rooppur NPP, your recommendation for operational documents "
           "'SAW not completed & Recommend to Revise' & 'Recommend to Revise' will be changed to"
           " 'SAW Not Completed & Document can be provisionally accepted considering the review comments' & Document can be provisionally accepted considering the review comments" )
    context = {"consent_msg":msg}
    if (UserConsentDocReviewRemarks.objects.filter(user=request.user).count() > 0):
        context = {"consent_given": True,"consent_msg":msg}
        return render(request, 'user_consent.html',context=context)

    if(request.method == 'POST'):
        if(request.POST.get('consent')!='agree'):
            return render(request, 'user_consent.html', context)
        else:
            a = UserConsentDocReviewRemarks.objects.create(user=request.user,consent_given_on=datetime.now(), consent_msg=msg)
            a.save()
            rs = ApprovalSignature.objects.filter(signed_by=request.user,remarks='recommend_to_revise').update(remarks='accept_with_remarks')
            nsrs = ApprovalSignature.objects.filter(signed_by=request.user,remarks='no_saw_recommend_to_revise').update(remarks='no_saw_accept_with_remarks')
            context = {"consent_given": True,"consent_msg":msg}
    return render(request,'user_consent.html',context)

def consent_correction(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if(not request.user.is_superuser):
        return redirect('/')
    if (request.method == 'GET'):
        return render(request, 'manpower/add_user_from_file.html')

    if (request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        count = 0
        row_count = 0
        for row in reader:
            if(row_count == 0):
                row_count += 1
                continue
            id = row[0]
            sign_hash = row[1]
            signed_on = row[2]
            remarks = row[3]

            if(remarks == 'recommend_to_revise'):
                user = ApprovalSignature.objects.get(id=id).signed_by
                if(UserConsentDocReviewRemarks.objects.filter(user=user).count() > 0):
                    ApprovalSignature.objects.filter(id=id).update(remarks='accept_with_remarks')
            elif(remarks == 'no_saw_recommend_to_revise'):
                user = ApprovalSignature.objects.get(id=id).signed_by
                if (UserConsentDocReviewRemarks.objects.filter(user=user).count() > 0):
                    ApprovalSignature.objects.filter(id=id).update(remarks='no_saw_accept_with_remarks')
            else:
                ApprovalSignature.objects.filter(id=id).update(remarks=remarks)
            row_count += 1
        response_msg = str(row_count)+" items updated"
        return HttpResponse(response_msg)