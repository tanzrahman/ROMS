from django.contrib import admin

from task_management.forms import UserSysSubSystemLinkForm, QuestionsForm
from task_management.models import *


class UserSysSubSystemLinkAdmin(admin.ModelAdmin):
    form = UserSysSubSystemLinkForm

class QuestionAdmin(admin.ModelAdmin):
    form = QuestionsForm
admin.site.register(UserSysSubSystemLink,UserSysSubSystemLinkAdmin)

admin.site.register(Questions,QuestionAdmin)
admin.site.register(QuestionsAnswers)
admin.site.register(Task)
admin.site.register(Activity)
admin.site.register(Comment)
admin.site.register(System)
admin.site.register(Facility)
admin.site.register(Milestone)
admin.site.register(SubSystem)
admin.site.register(SystemParameter)
admin.site.register(QuesChoices)
admin.site.register(ExecutorFeedBack)
admin.site.register(SupervisorFeedBack)
admin.site.register(TaskFeedBack)
admin.site.register(GroupMsgInstruction)
admin.site.register(DocumentRequest)
admin.site.register(MsgInstructionAction)
admin.site.register(Lecture)
admin.site.register(ConsultantLecture)
admin.site.register(ConsultantQA)
admin.site.register(ConsultantTasks)
admin.site.register(ConsultancyRequest)
admin.site.register(OperationalDocumentReview)
admin.site.register(RegulationDocumentReview)
admin.site.register(FireAndEmergencyDocumentReview)
admin.site.register(OthersDocumentReview)
admin.site.register(File)
admin.site.register(SecondTierDocumentReview)
admin.site.register(SecondTierCommitteeFeedback)
admin.site.register(DocumentReviewComments)
admin.site.register(SafetyAnalysisReportReview)
admin.site.register(SARCommitteeReport)
admin.site.register(TaskSupervisorLink)