from django.contrib import admin
from django.urls import path, include

import task_management.views as task_management
import task_management.doc_review_manager as doc_review

urlpatterns = [
	path('', task_management.homepage, name='task_management'),
	path('document_review/<action>', doc_review.doc_review_handler, name='doc_review_handler'),
	path('document_review/<action>/<id>', doc_review.doc_review_handler, name='doc_review_handler'),
	path('<action>', task_management.task_request_handler,name='task_request_handler'),
	path('<action>/', task_management.task_request_handler,name='task_request_handler'),
	path('<action>/<id>', task_management.task_request_handler,name='task_request_handler'),

	path('upload',task_management.upload_task,name='upload_task')

]