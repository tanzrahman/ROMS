from django.contrib import admin
from django.urls import path, include

import technical_solution.views as technical_solution

urlpatterns = [
	path('', technical_solution.homepage, name='ts_management'),
	path('ts/<action>', technical_solution.ts_request_handler,name='ts_request_handler'),
	path('<action>/', technical_solution.ts_request_handler,name='ts_request_handler'),
	path('<action>/<id>', technical_solution.ts_request_handler,name='ts_request_handler'),
	path('upload',technical_solution.upload_ts,name='upload_ts')

]