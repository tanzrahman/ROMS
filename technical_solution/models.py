from django.db import models
from django.utils import timezone
from manpower.models import User, Division, SubDepartment, DepartmentShop, Section, Profile,ApprovalSignature

from task_management.models import File
# Create your models here.
class TechnicalSolution(models.Model):
    id = models.AutoField(primary_key=True)
    sr_no = models.CharField(max_length=11,blank=True,null=True)
    ts_doc_code = models.CharField(max_length=512, blank=True,null=True)
    title = models.CharField(max_length=512, blank=True, null=True)

    ase_ref_letter = models.CharField(max_length=512, blank=True,null=True)
    ase_ref_letter_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    division = models.ForeignKey(Division,on_delete=models.DO_NOTHING, blank=True, null=True)
    shop = models.ManyToManyField(DepartmentShop)
    facility_kks = models.CharField(max_length=512, blank=True,null=True)
    relevant_wd_code = models.TextField(blank=True,null=True)
    reason_for_ts = models.TextField(blank=True,null=True)
    modification_type = models.CharField(max_length=512, blank=True,null=True)
    deadline_for_temporary_solution = models.DateField(blank=True, null=True)
    deadline_remarks = models.TextField(blank=True, null=True)

    ts_file = models.CharField(max_length=512,blank=True,null=True)


    class Meta:
        db_table = 'technical_solution'


    def shop_list(self):
        return list(self.shop.all())


class TechnicalSolutionReview(models.Model):
    id = models.AutoField(primary_key=True)
    technical_solution = models.ForeignKey(TechnicalSolution, on_delete=models.CASCADE)
    responsible_personnel = models.ManyToManyField(User, related_name='ts_responsible_personnel')
    review_personnel = models.ManyToManyField(User,related_name='ts_assigned_personnel')
    oesd_personnel = models.ManyToManyField(User,related_name='oesd_personnel')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ts_assigned_by')
    assigned_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ts_review'

class TSShopRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    technical_solution = models.ForeignKey(TechnicalSolution, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True,null=True)
    remarks_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ts_shop_remarks_from')
    remarks_date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table = 'ts_shop_remarks'

class TSOESDRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    technical_solution = models.ForeignKey(TechnicalSolution, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True,null=True)
    remarks_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ts_oesd_remarks_from')
    remarks_date = models.DateTimeField(default=timezone.now)
    class Meta:
        db_table = 'ts_oesd_remarks'

class TechnicalSolutionRecommendation(models.Model):
    id = models.AutoField(primary_key=True)
    technical_solution = models.ForeignKey(TechnicalSolution, on_delete=models.CASCADE)
    ts_review_team = models.ForeignKey(TechnicalSolutionReview, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    approval_signature = models.ManyToManyField(ApprovalSignature)
    class Meta:
        db_table = 'ts_recommendation'