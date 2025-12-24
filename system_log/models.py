import datetime

from django.db import models
from manpower.models import User, Profile
from task_management.models import Task
# Create your models here.

class UserLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True,default=datetime.datetime.now())
    ip = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'user_log'


class FileLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True,default=datetime.datetime.now())
    ip = models.CharField(max_length=256, blank=True, null=True)
    file_hash = models.CharField(max_length=256, blank=True, null=True)
    access_type = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'file_log'


class TaskLog(models.Model):
    id = models.AutoField(primary_key=True)
    changed_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(null=True)
    added_supervisor = models.TextField(max_length=1024, blank=True, null=True)
    added_executor = models.TextField(max_length=1024, blank=True, null=True)
    removed_supervisor = models.TextField(max_length=1024, blank=True, null=True)
    removed_executor = models.TextField(max_length=1024, blank=True, null=True)
    description = models.TextField(max_length=1024, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=True,default=1)
    ip = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'task_log'


class DocumentLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True, default=datetime.datetime.now())
    ip = models.CharField(max_length=256, blank=True, null=True)
    doc_id = models.CharField(max_length=256, blank=True, null=True)
    access_details = models.TextField(max_length=1024,blank=True,null=True)

    class Meta:
        db_table = 'document_log'


class FailedLoginLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True,default=datetime.datetime.now())
    ip = models.CharField(max_length=256, blank=True, null=True)
    login_attempt_count = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'failed_login_log'

class UserDeactivateLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True)
    ip = models.CharField(max_length=256, blank=True, null=True)
    deactivation_details = models.TextField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'user_deactivate_log'


class DocumentApprovalLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True)
    ip = models.CharField(max_length=256, blank=True, null=True)
    doc_id = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'document_approval_log'

class MailAndSMSLog(models.Model):
    id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    send_time = models.DateTimeField(null=True,default=datetime.datetime.now())
    phone_no = models.CharField(max_length=16, blank=True, null=True)
    email = models.CharField(max_length=128, blank=True, null=True)
    message_body = models.CharField(max_length=512, blank=True, null=True)
    sms_success = models.BooleanField(default=False)
    sms_error_reason = models.CharField(max_length=256,blank=True, null=True)
    email_error_reason = models.CharField(max_length=256,blank=True, null=True)
    email_success = models.BooleanField(default=False)

    class Meta:
        db_table = 'mail_sms_log'

class UserNotificationLog(models.Model):
    id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    time = models.DateTimeField(null=True)
    message_body = models.CharField(max_length=512, blank=True, null=True)
    viewed_at = models.DateTimeField(null=True)
    class Meta:
        db_table = 'user_notification_log'


class PasswordChangeLog(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=256, blank=True, null=True)
    time = models.DateTimeField(null=True)
    ip = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'password_change_log'

class NoticeBoard(models.Model):
    id = models.AutoField(primary_key=True)
    notice_header = models.TextField(blank=True, null=True)
    url_target = models.CharField(max_length=256,blank=True, null=True)
    notice = models.TextField(blank=True, null=True)
    expire_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'notice_board'

class ProfileEditLog(models.Model):
    id = models.AutoField(primary_key=True)
    changed_fields = models.TextField(blank=True, null=True, default='')
    changed_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    changed_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now())
    ip = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'profile_edit_log'