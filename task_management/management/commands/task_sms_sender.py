import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from task_management.models import *
from manpower.models import *
from task_management.notify_users import send_notification
import threading
from time import sleep
class Command(BaseCommand):
	help = "SMS Send Scheduler"

	def add_arguments(self, parser):
		parser.add_argument('--day', action='append', type=int)
		parser.add_argument('--month', action='append', type=int)
		parser.add_argument('--year', action='append', type=int)

	def handle(self, *args, **kwargs):
		
		month = kwargs['month'][0]
		year = kwargs['year'][0]
		div = Division.objects.get(division_name='Safety & Reliability')
		task_list = Task.objects.filter(planned_start_date__year=year, planned_end_date__month=month,status='N')
		if(kwargs.get('day')):
			day = int(kwargs.get('day')[0])
			task_list = task_list.filter(planned_start_date__day=day)

		print(task_list.count())
		count = 0
		for task in task_list:
			count += task.supervisor.all().count()
			count += task.task_executor.all().count()
			print(task.task_id,task.status)
			task.status='A'
			task.updated_date = datetime.date.today()	#set task assignment date to updated_date
			sleep(2)
			task.save()
			notifiyer = threading.Thread(target=send_notification, args=(task.id,))
			notifiyer.start()

		print("Total SMS to Send: ",count)





		
		
		
