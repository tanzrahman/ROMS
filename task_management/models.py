import datetime
from inspect import Signature

from django.db import models
from django.db.transaction import mark_for_rollback_on_error
from django.utils import timezone
from manpower.models import User, DepartmentShop, Division, Committee, ApprovalSignature, SafetyAnalysisReportCommittee


# Create your models here.

class SystemParameter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    value = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'system_parameter'


class System(models.Model):
    system_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    code = models.CharField(max_length=256, blank=True, null=True)
    short_description = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        db_table = 'system'

    def __str__(self):
        return str(self.name)
class SubSystem(models.Model):
    subsystem_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING,blank=True,null=True)

    class Meta:
        db_table = 'sub_system'

    def __str__(self):
        return str(self.name)
class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    short_description = models.CharField(max_length=512, blank=True, null=True)
    kks_code = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'facility'

    def __str__(self):
        return str(self.kks_code)

class Task(models.Model):
    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=256, blank=True, null=False, default="")
    division = models.ForeignKey(Division, on_delete=models.DO_NOTHING,blank=True,null=True)
    dept_id = models.ForeignKey(DepartmentShop, on_delete=models.DO_NOTHING, blank=True, null=True)
    milestone_id = models.CharField(max_length=256, blank=True, null=False, default="")
    stage = models.CharField(max_length=8, blank=True, null=False, default="")
    supervisor = models.ManyToManyField(User, related_name='supervisors')
    lead_supervisor = models.ForeignKey(User,on_delete=models.DO_NOTHING,blank=True,null=True,related_name='lead_supervisor')
    task_executor = models.ManyToManyField(User, related_name='executors')
    lead_executor = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True,related_name='lead_executor')
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING, blank=True, null=True)
    subsystem = models.ForeignKey(SubSystem, on_delete=models.DO_NOTHING, blank=True, null=True)
    facility = models.ForeignKey(Facility, on_delete=models.DO_NOTHING, blank=True, null=True)
    relevant_kks_codes = models.CharField(max_length=256, blank=True, null=True)
    task_created_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    title = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=512, blank=True, null=True)
    status = models.CharField(max_length=128,blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    updated_date = models.DateField(blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='updated_by')
    planned_start_date = models.DateField(blank=True, null=True)
    planned_end_date = models.DateField(blank=True, null=True)
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    percent_completed = models.IntegerField(blank=True, null=True,default=0)
    task_category = models.CharField(max_length=256, blank=True, null=False,default='CEW')

    class Meta:
        db_table = 'task'

    def __str__(self):
        if(self.milestone_id!=""):
            if(self.task_category == 'SAW'):
                if (self.task_id != ""):
                    return self.task_id
            return self.milestone_id

        if(self.task_id!=""):
            return self.task_id

        return self.title

    def supervisor_list(self):
        return list(self.supervisor.all())

    def executor_list(self):
        return list(self.task_executor.all())

    def executor_feedback(self,div):
        tfb = TaskFeedBack.objects.filter(task__id=self.id)
        if(tfb.count()>0):
            efb = tfb[0].executor_feedback.filter(approval_level=1, executor__profile__division=div)
            if(efb.count() > 0):
                return efb.first().id
        return None

class Activity(models.Model):
    activity_id = models.AutoField(primary_key=True)
    activity_executor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='activity_executor')
    task_id = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    file_id = models.CharField(max_length=256, blank=True, null=True)
    activity_created_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True,related_name='activity_created_by')
    activity_updated_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='activity_updated_by')
    title = models.CharField(max_length=256, blank=True, null=True)
    description = models.CharField(max_length=256, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    hours = models.IntegerField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    updated_date = models.DateField(blank=True, null=True)
    planned_start_date = models.DateField(blank=True, null=True)
    planned_end_date = models.DateField(blank=True, null=True)
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'activity'


class File(models.Model):
    hash = models.CharField(primary_key=True, max_length=256, null=False, blank=False)
    reference_count = models.IntegerField(blank=False, null=False, default=1)
    file_name = models.CharField(max_length=256, blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)
    file_size = models.CharField(max_length=20, blank=True, null=True)
    server_loc = models.CharField(max_length=512, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.file_type = self.file_name.split(".")[-1]
        super(File, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Custom logic before deletion
        from task_management.ftp_handler import delete_file
        delete_file(self.server_loc)
        super().delete(*args, **kwargs)
    class Meta:
        db_table = 'files'

class TaskSupervisorLink(models.Model):
    tslink_id = models.AutoField(primary_key=True)
    task_id = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    supervisor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task_opened_time = models.DateTimeField(blank=True, null=True)
    document_read = models.BooleanField(blank=True, null=True, default=False)
    task_acknowledged = models.BooleanField(blank=True, null=True, default=False)

    class Meta:
        db_table = 'task_supervisor_link'


class TaskExecutorLink(models.Model):
    te_link = models.AutoField(primary_key=True)
    task_id = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    executor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task_opened_time = models.DateTimeField(blank=True, null=True)
    document_read = models.BooleanField(blank=True,null=True,default=False)
    task_acknowledged = models.BooleanField(blank=True,null=True,default=False)
    class Meta:
        db_table = 'task_executor_link'


class ActivityExecutorLink(models.Model):
    ae_link = models.AutoField(primary_key=True)
    activity = models.ForeignKey(Activity, models.DO_NOTHING, blank=True, null=True)
    executor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        db_table = 'activity_executor_link'

class QuesChoices(models.Model):
    id = models.AutoField(primary_key=True)
    choice_1 = models.CharField(max_length=256, blank=True, null=False,default="")
    choice_2 = models.CharField(max_length=256, blank=True, null=False,default="")
    choice_3 = models.CharField(max_length=256, blank=True, null=False,default="")
    choice_4 = models.CharField(max_length=256, blank=True, null=False,default="")
    correct_choice = models.CharField(max_length=256, blank=True, null=False,default="")

    def __str__(self):
        return "{}, {}, {}, {}".format(self.choice_1, self.choice_2, self.choice_3, self.choice_4)
    class Meta:
        db_table = 'ques_choices'

class Questions(models.Model):
    id = models.AutoField(primary_key=True)
    task_state = models.CharField(max_length=16,blank=True,null=False,default="pre_start")
    task_category = models.CharField(max_length=16,blank=True,null=False,default="CEW")
    category = models.CharField(max_length=100, blank=True, null=False,default="")
    question = models.TextField(max_length=1024, blank=True, null=True)
    division = models.ForeignKey(Division,on_delete=models.DO_NOTHING,blank=True, null=True)
    task = models.ForeignKey(Task, models.DO_NOTHING,blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True, default=1)
    employee_category = models.CharField(max_length=64,blank=True, null=False, default='executor')
    choice = models.ForeignKey(QuesChoices, models.DO_NOTHING, blank=True, null=True)
    minimum_length = models.IntegerField(blank=True, null=True, default=200)

    def __str__(self):
        return '{}({},{},{},{})'.format(self.question,self.category,self.task_state,self.employee_category,self.priority)
    def que(self):
        return '{}'.format(self.question)
    class Meta:
        db_table = 'questions'


class QuestionsAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    task_id = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    task_question = models.ForeignKey(Questions, models.DO_NOTHING, blank=True, null=True)
    answer = models.TextField(max_length=1024, blank=True, null=True)
    answered_by = models.ForeignKey(User, models.DO_NOTHING,blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    is_approved = models.IntegerField(blank=True, null=True,default=0)
    class Meta:
        db_table = 'questions_answers'

    def is_correct(self):
        if(self.task_question.category == 'MCQ'):
            user_ans = self.answer.upper()
            correct_ans = self.task_question.choice.correct_choice.upper()
            if(correct_ans):
                if( user_ans not in correct_ans):
                    return False
        if(len(self.answer) < self.task_question.minimum_length):
            return False

        return True

class UserSysSubSystemLink(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    system = models.ManyToManyField(System, blank=True, null=True)
    sub_system = models.ManyToManyField(SubSystem,blank=True,null=True)

    class Meta:
        db_table = 'user_sys_subsystem_link'


class Milestone(models.Model):
    id = models.AutoField(primary_key=True)
    job_id = models.CharField(max_length=100, blank=False, null=False, default="")
    milestone_id = models.CharField(max_length=256, blank=True, null=False, default="")
    division = models.ForeignKey(Division, on_delete=models.DO_NOTHING, blank=True, null=True)
    facility = models.CharField(max_length=256, blank=True, null=False, default="")
    task_id = models.CharField(max_length=256, blank=True, null=False, default="")
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING, blank=True, null=True)
    category = models.CharField(max_length=8,blank=True,null=True,default='CE')
    title = models.CharField(max_length=256, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True,default=True)
    is_assigned = models.BooleanField(blank=True, null=True,default=False)
    is_completed = models.BooleanField(blank=False, null=False,default=False)

    class Meta:
        db_table = 'Milestone'

    def __str__(self):
        return str(self.milestone_id)


class ExecutorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    executor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'executor_feedback'

    def all_answers(self):
        return self.answers.all()

class SupervisorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    supervisor = models.ForeignKey(User,models.DO_NOTHING, blank=True,null=True)
    executor_feedback = models.ForeignKey(ExecutorFeedBack, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'supervisor_feedback'

class DistributorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    distributor = models.ForeignKey(User, models.DO_NOTHING,blank=True,null=True)
    executor_feedback = models.ForeignKey(ExecutorFeedBack, models.DO_NOTHING, blank=True, null=True)
    supervisor_feedback = models.ForeignKey(SupervisorFeedBack, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_at = models.DateTimeField(null=True)
    class Meta:
        db_table = 'distributor_feedback'

class TaskFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    executor_feedback = models.ManyToManyField(ExecutorFeedBack)
    supervisor_feedback = models.ManyToManyField(SupervisorFeedBack)
    distributor_feedback = models.ManyToManyField(DistributorFeedBack)
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'task_feedback'

    def all_ex_fb(self):
        return self.executor_feedback.filter(approval_level__gte=1)

    def all_sup_fb(self):
        return self.supervisor_feedback.filter(approval_level__gte=1)


class GroupMsgInstruction(models.Model):
    id = models.AutoField(primary_key=True)
    send_time = models.DateTimeField(null=True)
    message_body = models.CharField(max_length=256, blank=True, null=True)
    recipients = models.TextField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'group_msg_instruction'

    def __str__(self):
        return str(self.message_body)


class MsgInstructionAction(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    instruction = models.ForeignKey(GroupMsgInstruction, models.DO_NOTHING, blank=True, null=True)
    action_text = models.CharField(max_length=512, blank=True, null=True)
    file = models.ForeignKey(File, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'msg_instruction_action'


class DocumentRequest(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING,blank=True,null=True)

    requested_documents = models.TextField(max_length=1024, blank=True, null=True)
    requested_by = models.ForeignKey(User, models.DO_NOTHING,blank=True,null=True, related_name='requested_by')
    requested_at = models.DateTimeField(blank=True, null=True)
    received_at = models.DateTimeField(blank=True, null=True)
    requester_remarks = models.TextField(max_length=1024, blank=True, null=True)

    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='approved_by')
    approver_remarks = models.TextField(max_length=1024, blank=True, null=True)

    provided_documents = models.TextField(max_length=1024, blank=True, null=True)
    provider_remarks = models.TextField(max_length=1024, blank=True, null=True)
    provided_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='provided_by')
    provided_at = models.DateTimeField(blank=True, null=True)

    approval_level = models.IntegerField(blank=False, null=False, default=0)
    class Meta:
        db_table = 'document_request'


class Lecture(models.Model):
    id = models.AutoField(primary_key=True)
    tasks = models.ManyToManyField(Task)
    target_division = models.ForeignKey(Division,models.DO_NOTHING, blank=True, null=True)
    lecture_name = models.CharField(max_length=256, blank=True, null=True)
    lecture_category = models.CharField(max_length=256, blank=True, null=True)
    lecture_description = models.TextField(max_length=256, blank=True, null=True)
    venue = models.CharField(max_length=256, blank=True, null=True)
    schedule = models.DateTimeField(blank=True, null=True)
    lead_presenter = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=False, null=False,related_name='lead_presenter')
    other_presenter = models.ManyToManyField(User,related_name='other_presenter')
    special_participants = models.CharField(max_length=1024, blank=True, null=True)
    other_participants = models.ManyToManyField(User, related_name='other_participants')
    approval_level = models.IntegerField(blank=True, null=True)
    notified_users = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'lecture'

    def __str__(self):
        return self.lecture_name

class ExternalParticipants(models.Model):
    id = models.AutoField(primary_key=True)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    participants = models.TextField(max_length=3072, blank=True, null=True)

    class Meta:
        db_table = 'external_participants'

class LectureAttendance(models.Model):
    id = models.AutoField(primary_key=True)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, blank=True, null=True)
    attendance = models.TextField(max_length=4096, blank=True, null=True)

    class Meta:
        db_table = 'lecture_attendance'


class OngoingExecutorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    executor = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ongoing_executor_feedback'

    def all_answers(self):
        return self.answers.all()


class OngoingSupervisorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    supervisor = models.ForeignKey(User,models.DO_NOTHING, blank=True,null=True)
    executor_feedback = models.ForeignKey(ExecutorFeedBack, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'ongoing_supervisor_feedback'


class OngoingDistributorFeedBack(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    distributor = models.ForeignKey(User, models.DO_NOTHING,blank=True,null=True)
    executor_feedback = models.ForeignKey(ExecutorFeedBack, models.DO_NOTHING, blank=True, null=True)
    supervisor_feedback = models.ForeignKey(SupervisorFeedBack, models.DO_NOTHING, blank=True, null=True)
    answers = models.ManyToManyField(QuestionsAnswers, blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=False,default=0)
    created_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'ongoing_distributor_feedback'


class OnGoingTaskFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    executor_feedback = models.ForeignKey(OngoingExecutorFeedBack, models.DO_NOTHING, blank=True, null=True)
    supervisor_feedback = models.ForeignKey(OngoingSupervisorFeedBack, models.DO_NOTHING, blank=True, null=True)
    distributor_feedback = models.ForeignKey(OngoingDistributorFeedBack, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'ongoing_task_feedback'



class ConsultantTasks(models.Model):
    id = models.AutoField(primary_key=True)
    consultant = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(null=True)
    task = models.ForeignKey(Task, models.DO_NOTHING,blank=True,null=True)
    review_report = models.TextField(blank=True, null=True)
    report_submitted_at = models.DateTimeField(null=True)
    assigned_by = models.ForeignKey(User,on_delete=models.DO_NOTHING, blank=True, null=True, related_name="task_assigned_by")
    class Meta:
        db_table = 'consultant_tasks'

    def has_feedback(self):
        if(self.review_report):
            if(len(self.review_report)>10):
                return True
        return False
    def __str__(self):
        return self.task.__str__()
class ConsultantLecture(models.Model):
    id = models.AutoField(primary_key=True)
    consultant = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(null=True)
    lecture = models.ForeignKey(Lecture, models.DO_NOTHING, blank=True, null=True)
    report_submitted_at = models.DateTimeField(null=True)
    review_report = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="lecture_assigned_by")
    class Meta:
        db_table = 'consultant_lecture'

    def __str__(self):
        return str(self.id)+": "+self.consultant.__str__()+":\t "+self.lecture.__str__()


class ConsultantQA(models.Model):
    id = models.AutoField(primary_key=True)
    consultant = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='consultant')
    lecture = models.ForeignKey(Lecture, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(null=True)
    qa1 = models.TextField(blank=True, null=True)
    qa2 = models.TextField(blank=True, null=True)
    qa3 = models.ManyToManyField(User, related_name='best_participants')
    qa4 = models.TextField(blank=True, null=True)
    qa5 = models.TextField(blank=True, null=True)
    qa6 = models.TextField(blank=True, null=True)
    qa7 = models.TextField(blank=True, null=True)
    qa8 = models.TextField(blank=True, null=True)
    qa9 = models.ManyToManyField(User, related_name='participant_need_improvement')
    qa10 = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'consultant_QA'
    def __str__(self):
        return self.lecture.lecture_name


class LectureFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    participant = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    lecture = models.ForeignKey(Lecture, models.DO_NOTHING, blank=True, null=True)
    qa1 = models.TextField(blank=True, null=True)
    qa2 = models.TextField(blank=True, null=True)
    qa3 = models.TextField(blank=True, null=True)
    qa4 = models.TextField(blank=True, null=True)
    qa5 = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'lecture_feedback'


class ConsultancyRequest(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    requested_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True,related_name='consultancy_requested_by')
    task = models.ForeignKey(Task, models.DO_NOTHING, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    approval_status = models.IntegerField(blank=True, null=True)
    approved_by = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='consultancy_request_approved_by')
    approved_at = models.DateTimeField(null=True)
    message_for_consultant = models.TextField(blank=True, null=True)

    consultant = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True,related_name='consultant_on_requested_task')
    class Meta:
        db_table = 'consultancy_request'
    def __str__(self):
        return self.task.__str__()

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task_id = models.ForeignKey(Task, models.CASCADE, blank=True, null=True)
    activity_id = models.ForeignKey(Activity, models.CASCADE, blank=True, null=True)
    consultant_task_feedback = models.ForeignKey(ConsultantTasks,models.CASCADE,blank=True,null=True)
    consultant_qa = models.ForeignKey(ConsultantQA,models.CASCADE,blank=True,null=True)
    comment = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    action_id = models.CharField(max_length=100, blank=True, null=True)
    action_name = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'comment'

class OperationalDocumentReview(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task = models.ForeignKey(Task, models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=True)
    ######QUESTIONS#########
    version_of_doc = models.CharField(max_length=16, blank=True, null=True)
    eqipment_passport_code = models.CharField(max_length=256, blank=True, null=True)
    manufacturer_of_equipment = models.CharField(max_length=256, blank=True, null=True)
    safety_class = models.CharField(max_length=256, blank=True, null=True)
    quality_category = models.CharField(max_length=256, blank=True, null=True)
    seismic_category = models.CharField(max_length=256, blank=True, null=True)
    acceptance_criteria = models.TextField(blank=True, null=True)
    monitored_params = models.TextField(blank=True, null=True)
    params_reflected = models.TextField(blank=True, null=True)
    focusing_params= models.TextField(blank=True, null=True)
    safety_measures = models.TextField(blank=True, null=True)
    developed_for_rnpp = models.TextField(blank=True, null=True)
    transient_situation_explanation = models.TextField(blank=True, null=True)
    fulfill_design_requirements = models.TextField(blank=True, null=True)
    operational_modes_reflected = models.TextField(blank=True, null=True)
    align_with_scope_limit = models.TextField(blank=True, null=True)
    relevant_document_bd = models.TextField(blank=True, null=True)
    differences_reflected = models.TextField(blank=True, null=True)
    list_of_maloperations = models.TextField(blank=True, null=True)
    peripherial_important_params = models.TextField(blank=True, null=True)
    general_feedback = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'operational_document_review'

    def category(self):
        return "Operational"

    def __str__(self):
        return str(self.task.task_id)

    def save(self, *args, **kwargs):
        if(self.created_at == None):
            self.created_at = datetime.datetime.now()
            self.approval_level = 1
        self.modified_at = datetime.datetime.now()
        super(OperationalDocumentReview, self).save(*args, **kwargs)


class RegulationDocumentReview(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task = models.ForeignKey(Task, models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=True)
    ######QUESTIONS#########
    version_of_doc = models.CharField(max_length=16, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    storing_entity = models.TextField(blank=True, null=True)
    is_applicable = models.TextField(blank=True, null=True)
    specific_users_of_document = models.TextField(blank=True, null=True)
    other_users_of_document = models.TextField(blank=True, null=True)
    user_qualification = models.TextField(blank=True, null=True)
    safety_measures = models.TextField(blank=True, null=True)
    record_of_work = models.TextField(blank=True, null=True)
    deviation_notification_reporting = models.TextField(blank=True, null=True)
    next_review_date = models.DateField(blank=True, null=True)
    next_review_dept_person = models.TextField(blank=True, null=True)
    test_procedures_valid_logical = models.TextField(blank=True, null=True)
    limits_of_normal_operations = models.TextField(blank=True, null=True)
    reason_to_keep_gost_docs = models.TextField(blank=True, null=True)
    general_feedback = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'regulation_document_review'

    def __str__(self):
        return str(self.task.task_id)

    def category(self):
        return "Regulation"


    def save(self, *args, **kwargs):
        if(self.created_at == None):
            self.created_at = datetime.datetime.now()
            self.approval_level = 1
        self.modified_at = datetime.datetime.now()
        super(RegulationDocumentReview, self).save(*args, **kwargs)


class FireAndEmergencyDocumentReview(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task = models.ForeignKey(Task, models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=True)
    ######QUESTIONS#########
    version_of_doc = models.CharField(max_length=16, blank=True, null=True)
    equipment_passport_code = models.CharField(max_length=256, blank=True, null=True)
    safety_class = models.CharField(max_length=256, blank=True, null=True)
    quality_category = models.CharField(max_length=256, blank=True, null=True)
    seismic_category = models.CharField(max_length=256, blank=True, null=True)
    hydrant_piping_acceptance_criteria = models.TextField(blank=True, null=True)
    success_criteria_params = models.TextField(blank=True, null=True)
    bangladesh_compliance = models.TextField(blank=True, null=True)
    bd_standard_practice = models.TextField(blank=True, null=True)
    compliance_waste_water_accum = models.TextField(blank=True, null=True)
    fire_drill_frequency = models.TextField(blank=True, null=True)
    steps_need_to_take = models.TextField(blank=True, null=True)
    safety_gear_standards = models.TextField(blank=True, null=True)
    water_level_bd_compliance = models.TextField(blank=True, null=True)
    foam_flooding_scope = models.TextField(blank=True, null=True)
    role_of_personnel = models.TextField(blank=True, null=True)
    align_with_rnpp = models.TextField(blank=True, null=True)
    general_feedback = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'fire_emergency_document_review'

    def __str__(self):
        return str(self.task.task_id)

    def category(self):
        return "Fire"


    def save(self, *args, **kwargs):
        if(self.created_at == None):
            self.created_at = datetime.datetime.now()
            self.approval_level = 1
        self.modified_at = datetime.datetime.now()
        super(FireAndEmergencyDocumentReview, self).save(*args, **kwargs)


class OthersDocumentReview(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    task = models.ForeignKey(Task, models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    approval_level = models.IntegerField(blank=True, null=True)
    #####DOC SPECIFIC FIELDS########
    document_category = models.CharField(max_length=256, blank=True, null=True)
    version_of_doc = models.CharField(max_length=16, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    storing_entity = models.TextField(blank=True, null=True)
    for_bd = models.TextField(blank=True, null=True)
    users_of_document = models.TextField(blank=True, null=True)
    general_feedback = models.TextField(blank=True, null=True)


    def __str__(self):
        return str(self.task.task_id)

    def category(self):
        return "Other"

    def save(self, *args, **kwargs):
        if (self.created_at == None):
            self.created_at = datetime.datetime.now()
            self.approval_level = 1
        self.modified_at = datetime.datetime.now()
        super(OthersDocumentReview, self).save(*args, **kwargs)

class SecondTierDocumentReview(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField(max_length=128, blank=True, null=True)
    op_doc_review = models.ForeignKey(OperationalDocumentReview, on_delete=models.CASCADE, blank=True, null=True)
    regulation_doc_review = models.ForeignKey(RegulationDocumentReview, on_delete=models.CASCADE, blank=True, null=True)
    fire_doc_review = models.ForeignKey(FireAndEmergencyDocumentReview, on_delete=models.CASCADE, blank=True, null=True)
    other_doc_review = models.ForeignKey(OthersDocumentReview, on_delete=models.CASCADE, blank=True, null=True)

    committee = models.ForeignKey(Committee, on_delete=models.DO_NOTHING, blank=True, null=True)
    assigned_date = models.DateField(blank=True, null=True)
    committee_deadline = models.DateField(blank=True, null=True)

    committee_approval = models.ManyToManyField(ApprovalSignature, related_name='second_tier_committee_approval', blank=True, null=True)
    division_head_approval = models.ForeignKey(ApprovalSignature, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='division_head_approval')
    chief_eng_approval = models.ForeignKey(ApprovalSignature, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='chief_eng_approval')
    sd_approval = models.ForeignKey(ApprovalSignature, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='sd_approval')

    class Meta:
        db_table = 'second_tier_document_review'
    def __str__(self):
        return str(self.task.task_id)


class SecondTierCommitteeFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    committee = models.ForeignKey(Committee, on_delete=models.DO_NOTHING, blank=True, null=True)
    feedback_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    feedback_date = models.DateField(blank=True, null=True)
    approval_or_revise = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = 'second_tier_committee_feedback'


class DocumentReviewComments(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, blank=True, null=True)
    second_tier_committee_review = models.ForeignKey(SecondTierDocumentReview, on_delete=models.DO_NOTHING, blank=True, null=True)
    proposed_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='review_comment_proposed_by')
    created_at = models.DateTimeField(blank=True, null=True)
    #######PTD APPROVED QUESTION/ANS TABLE#########

    ###### RNPP SIDE############
    section_no = models.CharField(max_length=256, blank=True, null=True)
    original_text = models.TextField(blank=True, null=True)
    proposed_text = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    ###### END OF RNPP SIDE############

    #########CREA/ RUSSIAN SIDE #############
    replied_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='review_comment_replied_by')
    reply_on = models.DateTimeField(blank=True, null=True)
    proposal_acceptance = models.TextField(blank=True, null=True)   # accepted or not accepted or partially accepted
    reply_remarks = models.TextField(blank=True, null=True)
    ######### END of CREA/ RUSSIAN SIDE #############

    class Meta:
        db_table = 'document_review_comments'


# class DocumentReviewComments_MD(models.Model):
#     id = models.AutoField(primary_key=True)
#     task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, blank=True, null=True)
#     second_tier_committee_review = models.ForeignKey(SecondTierDocumentReview, on_delete=models.DO_NOTHING, blank=True, null=True)
#     remarks_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='review_comment_remarks_by')
#     created_at = models.DateTimeField(blank=True, null=True)
#     remarks = models.TextField(blank=True, null=True)
#     class Meta:
#         db_table = 'document_review_comments_MD'


class SafetyAnalysisReportReview(models.Model):
    id = models.AutoField(primary_key=True)
    committee = models.ForeignKey(SafetyAnalysisReportCommittee, on_delete=models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User,  on_delete=models.DO_NOTHING, blank=True, null=True,related_name='sar_chapter_reviewer')
    assigned_section = models.CharField(max_length=1024, blank=True, null=True)
    assigned_section_title = models.CharField(max_length=2048, blank=True, null=True)
    analysis_report_file = models.CharField(max_length=256, blank=True, null=True)
    assigned_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)
    assign_date = models.DateField(blank=True, null=True)
    submitted_on = models.DateTimeField(blank=True, null=True, default=timezone.now)
    submitted_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='sar_submitted_by')

    class Meta:
        db_table = 'safety_analysis_report_review'

    def __str__(self):
        text = "{}: {}, {}".format(self.user, self.assigned_section, self.assigned_section_title)
        return text

class SARCommitteeReport(models.Model):
    id = models.AutoField(primary_key=True)
    committee = models.ForeignKey(SafetyAnalysisReportCommittee, on_delete=models.CASCADE, blank=True, null=True)
    analysis_report_file = models.CharField(max_length=256, blank=True, null=True)
    submitted_on = models.DateTimeField(blank=True, null=True, default=timezone.now)
    submitted_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='sar_cmt_report_submitted_by')
    class Meta:
        db_table = 'sar_committee_report'

    def __str__(self):
        return str(self.committee.name)


