import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from task_management.models import *
from manpower.models import *
from task_management.notify_users import send_notification
import threading
from time import sleep
class Command(BaseCommand):
	help = "Task Deleter"

	def add_arguments(self, parser):
		parser.add_argument('--id', action='append', type=int)
		parser.add_argument('--task', action='append', type=str, required=False)
		parser.add_argument('--mid', action='append', type=str, required=False)
		parser.add_argument('--command', action='append', type=str)

	def handle(self, *args, **kwargs):
		task = None
		id = None
		command = None
		mid = None
		if(kwargs.get('id')):
			id = kwargs['id'][0]

		if(kwargs.get('task')):
			task = kwargs['task'][0]

		if(kwargs.get('mid')):
			mid = kwargs['mid'][0]

		if (kwargs.get('command')):
			command = kwargs['command'][0]

		if(command == "info"):
			tasks = []

			if(task):
				tasks = Task.objects.filter(task_id=task)
			else:
				tasks = Task.objects.filter(milestone_id=mid)
				task = mid

			print("---------------All information about the task: " + task + "------------------")
			print("Total number of tasks: "+str(tasks.count()))
			print("---------------Details: " + task + "------------------")
			count = 0
			for each in tasks:
				count = count + 1
				print("----------------------------------------------------------------------")
				print(str(count)+". Task ID", each.id)
				print("Supervisors: ",each.supervisor_list())
				print("Executors: ",each.executor_list())
				print("Feedbacks: ", each.taskfeedback_set.all())
				print("Executor Feedbacks: ",each.executorfeedback_set.all())
				print("Supervisor Feedbacks: ",each.supervisorfeedback_set.all())
				print("Task Supervisor Link: ",each.tasksupervisorlink_set.all())
				print("Task Executor Link: ",each.taskexecutorlink_set.all())
				print("Lectures: ",each.lecture_set.all())
				print("Document Request Set: ", each.documentrequest_set.all())
				print("Consultancy Requests: ",each.consultancyrequest_set.all())
				print("Consultant Tasks: ",each.consultanttasks_set.all())
				print("Comments: ",each.comment_set.all())
				print("Task Logs: ",each.tasklog_set.all())
				print("Work progress Feedback: ",each.ongoingtaskfeedback_set.all())
				print("Work progress Executor Feedback: ", each.ongoingexecutorfeedback_set.all())
				print("Work progress supervisor Feedback: ", each.ongoingsupervisorfeedback_set.all())
				print("Question Answers: ",each.questionsanswers_set.all())
				print("Question : ",each.questions_set.all())
				print("----------------------------------------------------------------------\n\n\n")

		if (command == "delete"):
			print("----------------------------------------------------------------------")
			print("Deleting Task ID", id)
			task = Task.objects.get(id=id)

			print("----Removing Supervisors---")
			sup = task.supervisor.all()
			for each in sup:
				print(each)
				task.supervisor.remove(each)

			print("----Removing Executors---")
			exec = task.task_executor.all()
			for each in exec:
				print(each)
				task.task_executor.remove(each)

			print("------Removing Task Supervisor Link------")
			sup_link = task.tasksupervisorlink_set.all()
			for each in sup_link:
				print(each)
				task.tasksupervisorlink_set.remove(each)

			print("------Removing Task Executor Link------")
			exec_link = task.taskexecutorlink_set.all()
			for each in exec_link:
				print(each)
				task.taskexecutorlink_set.remove(each)

			print("--------Removing Comments---------------")
			comments = task.comment_set.all()
			for each in comments:
				print(each)
				each.delete()

			print("-------Removing Consultancy Requests---------------")
			con_req = task.consultancyrequest_set.all()
			for each in con_req:
				print(each)
				each.delete()

			print("--------Removing Document Requests---------------")
			docs = task.documentrequest_set.all()
			for each in docs:
				print(each)
				each.delete()

			print("--------Removing task from Lecture---------")
			lectures = task.lecture_set.all()
			for each in lectures:
				print("Removing from lecture: ",each)
				each.tasks.remove(task)


			print("----------Removing Task Log----------")
			task_log = task.tasklog_set.all()
			for each in task_log:
				print(each)
				each.delete()


			print("--------Removing Task Feedbacks ----------")
			fb = task.taskfeedback_set.all()
			print("Deleting Feedbacks-")
			for each in fb:
				print(each)
				each.delete()

			print("Deleting Supervisor Feedbacks-")
			sfb = task.supervisorfeedback_set.all()
			for each in sfb:
				print(each)
				each.delete()

			print("Deleting Executor Feedbacks-")
			efb = task.executorfeedback_set.all()
			for each in efb:
				print(each)
				each.delete()

			print("Deleting Ongoing Task Feedbacks-")
			otf = task.ongoingtaskfeedback_set.all()
			for each in otf:
				print(each)
				each.delete()

			osf = task.ongoingsupervisorfeedback_set.all()
			for each in osf:
				print(each)
				each.delete()

			oef = task.ongoingexecutorfeedback_set.all()
			for each in oef:
				print(each)
				each.delete()


			print("---------Removing Task Question Answers-----------")
			qas = task.questionsanswers_set.all()
			for each in qas:
				print(each)
				each.delete()

			print("------Removing Task -----")
			task.delete()
		
		
		
