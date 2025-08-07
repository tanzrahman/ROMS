from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Division(models.Model):
    div_id = models.AutoField(primary_key=True)
    division_name = models.CharField(max_length=64, blank=False, null=False)
    def __str__(self):
        return self.division_name

class DepartmentShop(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=256, blank=True, null=True)
    dept_code = models.CharField(max_length=256, blank=False, null=False, default="")
    class Meta:
        db_table = 'department_shop'

    def __str__(self):
        return self.dept_name


class Section(models.Model):
    section_id= models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=256, blank=False, null=False)
    section_details = models.CharField(max_length=256, blank=True, null=True)
    def __str__(self):
        return self.section_name

class SubDepartment(models.Model):
    subdepartment_id= models.AutoField(primary_key=True)
    subdepartment_name = models.CharField(max_length=256, blank=False, null=False)
    def __str__(self):
        return self.subdepartment_name


class IPWhitelist(models.Model):
    id = models.AutoField(primary_key=True)
    ip_address = models.CharField(max_length=256, blank=True, null=True)
    subnet = models.IntegerField(blank=True, null=True)
    country_code = models.CharField(max_length=16, blank=True, null=True)
    version = models.CharField(max_length=16, blank=True, null=True)
    denied = models.IntegerField(blank=True, null=True,default=1)

    class Meta:
        db_table = 'ip_whitelist'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.DO_NOTHING, blank=True, null=True)
    department = models.ForeignKey(DepartmentShop, models.DO_NOTHING, blank=True, null=True)
    npcbl_designation = models.CharField(max_length=256, blank=True, null=True)
    designation = models.CharField(max_length=256, blank=True, null=True)
    section = models.ForeignKey(Section, models.DO_NOTHING, blank=True, null=True)
    subdepartment = models.ForeignKey(SubDepartment, models.DO_NOTHING, blank=True, null=True)
    employee_id = models.CharField(max_length=16, blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)
    is_supervisor = models.BooleanField(blank=False, null=False, default=False)
    is_executor = models.BooleanField(blank=False, null=False, default=True)
    access_level = models.IntegerField(null=False, blank=False, default=0)
    email_validation_token = models.CharField(blank=True, null=True, max_length=128)
    signature = models.CharField(max_length=256, blank=True, null=True)
    validation_expire_date_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        user = self.user
        name = user.username + "(" + str(self.designation) + ")"
        return name

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if (created):
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

def get_user_details(self):
    if(self.groups.filter(name='consultant').count()>0):
        consultant = "{}({})".format(self.username,self.profile.department.__str__())
        return consultant
    return self.username

User.add_to_class("__str__", get_user_details)

class Committee(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=512, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.DO_NOTHING, blank=True, null=True)
    department = models.ForeignKey(DepartmentShop, on_delete=models.DO_NOTHING, blank=True, null=True)
    members = models.ManyToManyField(User, related_name='members')
    lead = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    div_head = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='divisional_head')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'committee'

class ApprovalSignature(models.Model):
    id = models.AutoField(primary_key=True)
    sign_hash = models.CharField(max_length=512, blank=True, null=True)
    signed_on = models.DateField(blank=True, null=True)
    signed_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    remarks = models.CharField(max_length=512, blank=True, null=True)
    remarks_1 = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        db_table = 'approval_signature'


class SafetyAnalysisReportCommittee(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=512, blank=True, null=True)
    sar_section = models.CharField(max_length=512, blank=True, null=True)
    sar_section_title = models.CharField(max_length=512, blank=True, null=True)
    members = models.ManyToManyField(User, related_name='sar_members')
    lead = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name

class UserConsentDocReviewRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consent_msg = models.CharField(max_length=512, blank=True, null=True)
    consent_given_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_consent_doc_review_remarks'
