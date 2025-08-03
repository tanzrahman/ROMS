from django.http import HttpResponse
from django.shortcuts import render
from technical_solution.models import *
from technical_solution.manage_ts import *
import datetime
# Create your views here.

def homepage(request):
    return render(request, 'technical_solution/ts_base.html')

def ts_request_handler(request, action):
    if (action == 'ts_list'):
        return ts_list(request)
    else:
        return HttpResponse("Invalid Access")

def upload_ts(request):

    context = {}
    output = open("errors.csv","w")
    if(request.method == 'POST'):
        file = request.FILES['user_csv'].file.read()
        reader = csv.reader(StringIO(file.decode('utf-8')))
        row_count = 0
        for row in reader:

            row_count += 1
            if(row_count == 1):
                # ignore first row
                continue

            # Assign values to variables based on the sequence
            sr_no = row[0]
            folder_number = row[1]
            ts_title = row[2]
            ts_id = row[3]
            ase_letter_ref = row[4]
            ase_letter_date = row[5]
            facility_kks_code = row[6]
            division = row[7]
            responsible_shop = row[8]
            wd_code_related_to_ts = row[9]
            reason_for_ts = row[10]
            modification_type = row[11]
            deadline_for_resolution = row[12]
            deadline_for_resolution_remarks = row[13]
            status_of_ts = row[14]
            try:
                if(division != ""):
                    division = Division.objects.get(division_name=division)
                else:
                    division = None

                if(responsible_shop != ""):
                    if(DepartmentShop.objects.filter(dept_code=responsible_shop).count()>0):
                        responsible_shop = DepartmentShop.objects.get(dept_code=responsible_shop)
                    else:
                        responsible_shop = None

                if(ase_letter_date != ""):
                    ase_letter_date = datetime.datetime.strptime(ase_letter_date,"%Y-%m-%d").date()
                else:
                    ase_letter_date = None

                if(deadline_for_resolution != ""):
                    deadline_for_resolution = datetime.datetime.strptime(deadline_for_resolution,"%Y-%m-%d").date()
                else:
                    deadline_for_resolution = None
                # Create and save a new TechnicalSolution object
                try:
                    ts = TechnicalSolution.objects.create(
                        sr_no=sr_no, title=ts_title, ts_doc_code=ts_id, ase_ref_letter=ase_letter_ref, ase_ref_letter_date=ase_letter_date,
                        facility_kks=facility_kks_code, division=division,
                        relevant_wd_code=wd_code_related_to_ts, reason_for_ts=reason_for_ts,
                        modification_type=modification_type, deadline_for_temporary_solution=deadline_for_resolution,
                        deadline_remarks=deadline_for_resolution_remarks)
                    if(responsible_shop):
                        ts.shop.add(responsible_shop)
                    print(ts.ts_doc_code)
                except Exception as e:
                    msg = "{},'{}'\n".format(ts_id,e.__str__())
                    print(msg)
                    output.write(msg)
            except Exception as e:
                msg = "{},'{}'\n".format(ts_id, e.__str__())
                print(msg)
                output.write(msg)

        output.close()
        return HttpResponse("Success")
    return render(request,'manpower/add_user_from_file.html')
