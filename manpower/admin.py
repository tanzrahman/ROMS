from django.contrib import admin
from django.contrib import admin
from manpower.models import IPWhitelist, DepartmentShop, Profile, Section, SubDepartment, Division, Committee
from manpower.models import ApprovalSignature, SafetyAnalysisReportCommittee

admin.site.register(Division)
admin.site.register(IPWhitelist)
admin.site.register(Profile)
admin.site.register(DepartmentShop)

admin.site.register(Section)
admin.site.register(SubDepartment)
admin.site.register(Committee)
admin.site.register(ApprovalSignature)
admin.site.register(SafetyAnalysisReportCommittee)
