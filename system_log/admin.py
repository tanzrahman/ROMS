from django.contrib import admin
from django.contrib import admin
from manpower.models import IPWhitelist, DepartmentShop, Profile
from system_log.models import *

admin.site.register(UserLog)
admin.site.register(FailedLoginLog)
admin.site.register(FileLog)
admin.site.register(MailAndSMSLog)
admin.site.register(TaskLog)
admin.site.register(NoticeBoard)