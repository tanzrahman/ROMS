import threading
import datetime
import json
from django.core import paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.forms import formset_factory, modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from task_management.models import Task, DistributorFeedBack, Questions, QuestionsAnswers, QuesChoices, File
from task_management.models import ExecutorFeedBack, SupervisorFeedBack, TaskFeedBack, OngoingSupervisorFeedBack
from task_management.models import OnGoingTaskFeedback, OngoingExecutorFeedBack, OngoingDistributorFeedBack
from task_management.notify_users import send_notification, send_notification_non_departmental
from task_management.system_list import systems as system_list
from task_management.forms import QuestionsForm,QuestionsAnswersForm, OngoingTaskQuestionAnswer
from task_management.milestone_handler import milestone_list
from task_management.milestone_handler import verify_milestones
import csv
from io import StringIO
from task_management.notify_users import send_task_list_notification
from time import sleep
from task_management.ftp_handler import upload_to_ftp,fetch_file

def add_question_answer(request, task_id):

    task = Task.objects.get(id=int(task_id))
    task_feed_back = TaskFeedBack.objects.filter(task=task)
    no_of_questions = 0
    ex_feed_back = None
    sup_feed_back = None
    tfb = None
    # create task feedback
    if (task_feed_back.count() < 1):
        tfb = TaskFeedBack.objects.create(task=task,created_at=datetime.datetime.now())
    else:
        tfb = task_feed_back.first()

    init_context = {'user': request.user, 'task_id': task_id}
    if(request.user in task.supervisor.all()):

        init_context.update({
            'user_category':'supervisor'
        })
        no_of_questions = Questions.objects.filter(employee_category='supervisor').count()
    elif(request.user in task.task_executor.all()):

        init_context.update({
            'user_category': 'executor'
        })
        no_of_questions = Questions.objects.filter(employee_category='executor').count()
    else:
        if(task.division == request.user.division):
            if(request.user.profile.access_level == 5):
                init_context.update({
                    'user_category': 'distributor'
                })


    #check last ques answers
    #set default question priority = 0
    priority = 0
    user_answer_list = QuestionsAnswers.objects.filter(task_id=task,answered_by=request.user).order_by('id')
    if(user_answer_list.count()>0):
        priority = user_answer_list.last().task_question.priority
        if(not user_answer_list.last().is_correct()):
            priority -= 1

    init_context.update({
        'priority': priority
    })
    form = QuestionsAnswersForm(initial=init_context)

    context = {'form':form,'task':task,'qa_list':user_answer_list}
    if (no_of_questions <= init_context['priority']):
        context.update({'qa_complete': True})

    # if executor feedback availavle in query string, load data
    if (request.GET.get('exec_fb')):
        ex_fb_id = int(request.GET.get('exec_fb'))
        executor_feed_back = ExecutorFeedBack.objects.get(id=ex_fb_id)
        context.update({'exec_feed_back':executor_feed_back})


    if(request.method == 'GET'):
        return render(request, 'task_management/add_answer.html', context)

    if(request.method == 'POST'):
        form = QuestionsAnswersForm(request.POST, initial=init_context)
        qa_complete = False
        if (request.POST.get('commit')):
            qa_complete = True

        if(form.is_valid()):
            answer = None
            add_answer = form.save()

            add_answer.answered_by = request.user
            add_answer.created_at = datetime.datetime.today()
            add_answer.task_id = task
            add_answer.save()

            answer = add_answer

            if(init_context.get('user_category') == 'executor'):
                feed_back = ExecutorFeedBack.objects.filter(task=task,executor=request.user)

                if(feed_back.count()<1):
                    ex_feed_back = ExecutorFeedBack.objects.create(task=task,executor=request.user)
                    ex_feed_back.answers.add(answer)
                    ex_feed_back.save()
                else:
                    ex_feed_back = feed_back.first()
                    ex_feed_back.answers.add(answer)
                    ex_feed_back.save()

            if (init_context.get('user_category') == 'supervisor'):
                feed_back = SupervisorFeedBack.objects.filter(task=task, supervisor=request.user)
                if(feed_back.count()<1):
                    curr_time = datetime.datetime.now()
                    sup_feed_back = SupervisorFeedBack.objects.create(task=task, supervisor=request.user,created_at=curr_time)
                    sup_feed_back.answers.add(answer)
                    sup_feed_back.save()
                else:
                    sup_feed_back = feed_back.first()
                    sup_feed_back.answers.add(answer)
                    sup_feed_back.save()

            if (ex_feed_back):
                if(qa_complete):
                    ex_feed_back.approval_level += 1
                    ex_feed_back.save()
                tfb.executor_feedback.add(ex_feed_back)

            if (sup_feed_back):
                if (qa_complete):
                    sup_feed_back.approval_level += 1
                    sup_feed_back.save()
                tfb.supervisor_feedback.add(sup_feed_back)

            init_context.update({
                'priority':priority+1
            })
            if (not user_answer_list.last().is_correct()):
                init_context.update({
                    'priority': priority
                })

            form = QuestionsAnswersForm(initial=init_context)
            context.update({'form':form})
            message = "You've answered {} question out of {}".format(init_context['priority'], no_of_questions)

            if(qa_complete):
                context.update({'fb_complete': "Feedback Completed"})

            context.update({'message':message})
        if(init_context['priority'] == no_of_questions-1 ):
            context.update({'qa_complete':True})


        return render(request, 'task_management/add_answer.html', context)



def edit_answer(request,qid):

    qa = QuestionsAnswers.objects.get(id=qid)
    task = qa.task_id
    if(qa.answered_by != request.user):
        return HttpResponse("You cannot change someone elses answer")
    else:
        init_context = {'user': request.user, 'task_id': task}
        if (request.user in task.supervisor.all()):

            init_context.update({
                'user_category': 'supervisor'
            })
        elif (request.user in task.task_executor.all()):

            init_context.update({
                'user_category': 'executor'
            })
        else:
            if (task.division == request.user.division):
                if (request.user.profile.access_level == 5):
                    init_context.update({
                        'user_category': 'distributor'
                    })

        init_context.update({
            'priority': qa.task_question.priority-1
        })
        form = QuestionsAnswersForm(initial=init_context,instance=qa)

        if(request.method == 'POST'):
            ans = QuestionsAnswersForm(request.POST,initial=init_context,instance=qa)
            if(ans.is_valid()):
                ans.save()
    return render(request,'task_management/add_answer.html', {'form':form})


def executor_feedback(request,task_id):
    task = Task.objects.get(id=task_id)
    user = request.user
    if(user not in task.task_executor.all()):
        return HttpResponse("You do not have permission to give feedback in this task")

    context = {'task':task}


    if(request.method == 'GET'):
        fb = ExecutorFeedBack.objects.filter(executor=request.user, task_id=task)
        if (fb.count() > 0):
            return HttpResponse("You already have given feedback in this task")
        return render(request, 'task_management/executor_feedback.html', context)

    if(request.method == 'POST'):
        fb = ExecutorFeedBack.objects.filter(executor=request.user, task_id=task)
        if (fb.count() > 0):
            return HttpResponse("You already have given feedback in this task")
        exec_feedback = None
        if(fb.count()>0):
            exec_feedback = fb.first()
        else:
            exec_feedback = ExecutorFeedBack.objects.create(task=task, executor=request.user, approval_level=1,
                                                            created_date=datetime.datetime.now())
        for each in request.POST.keys():
            if('answer' in each):
                que_priority = each.split('_')[1]
                answer = request.POST[each]
                question = Questions.objects.get(priority=que_priority, employee_category='executor',task_state='pre_start')
                q_answer = QuestionsAnswers.objects.create(task_id=task, answered_by=request.user,
                                                           task_question=question, answer=answer,
                                                           is_approved=1,created_at=datetime.datetime.now())
                exec_feedback.answers.add(q_answer)

        exec_feedback.save()

        tfb = TaskFeedBack.objects.filter(task=task)
        task_feedback = None
        if(tfb.count()>0):
            task_feedback = tfb.first()
        else:
            task_feedback = TaskFeedBack.objects.create(task=task,created_at=datetime.datetime.now())

        task_feedback.executor_feedback.add(exec_feedback)

        context.update({'success':'success'})
        return render(request, 'task_management/executor_feedback.html', context)



def supervisor_feedback(request,task_id):

    task = Task.objects.get(id=int(task_id))
    user = request.user
    if(user not in task.supervisor.all()):
        return HttpResponse("You do not have permission to give feedback in this task")

    context = {'task': task}

    exec_feed_back = None
    if(request.GET.get('exec_fb')):
        exec_feed_back = int(request.GET.get('exec_fb'))
        executor_feed_back = ExecutorFeedBack.objects.get(id=exec_feed_back)
        exec_qa = executor_feed_back.answers.all().order_by('task_question__priority')

        if(SupervisorFeedBack.objects.filter(supervisor=request.user, task_id=task,executor_feedback=executor_feed_back).count()>0):
            return HttpResponse("You've already have feedback in this task against the same executor")

        exec_qa_list = list(exec_qa.values_list('task_question__priority', flat=True))
        executor = executor_feed_back.executor
        context.update({'exec_qa': exec_qa, 'executor': executor,'total_qa':exec_qa.count()})

    if (request.method == 'POST'):
        fb = SupervisorFeedBack.objects.filter(supervisor=request.user, task_id=task)
        sup_feedback = None
        if (fb.count() > 0):
            sup_feedback = fb.first()
        else:
            curr_time = datetime.datetime.now()
            sup_feedback = SupervisorFeedBack.objects.create(task=task, supervisor=request.user, approval_level=1,
                                                             created_at=curr_time)
        for each in request.POST.keys():
            if ('answer' in each):
                que_priority = each.split('_')[1]
                answer = request.POST[each]
                question = Questions.objects.get(priority=que_priority, employee_category='supervisor',task_state='pre_start')
                q_answer = QuestionsAnswers.objects.create(task_id=task, answered_by=request.user,
                                                           task_question=question, answer=answer,
                                                           is_approved=1,created_at=datetime.datetime.now())
                sup_feedback.answers.add(q_answer)

        sup_feedback.executor_feedback = executor_feed_back
        sup_feedback.save()

        executor_feed_back.approval_level += 1
        executor_feed_back.save()

        tfb = TaskFeedBack.objects.filter(task=task)
        task_feedback = None
        if (tfb.count() > 0):
            task_feedback = tfb.first()
        else:
            curr_time = datetime.datetime.now()
            task_feedback = TaskFeedBack.objects.create(task=task,created_at=curr_time)

        task_feedback.supervisor_feedback.add(sup_feedback)

        context.update({'success': 'success'})

    return render(request,'task_management/supervisor_feedback.html', context)


def ongoing_executor_feedback(request,tid):

    task = Task.objects.get(id=tid)
    if(not request.user in task.task_executor.all()):
        return HttpResponse("You do not have permission to give feedback in this task")

    if(ExecutorFeedBack.objects.filter(task=task,executor=request.user).count()<1):
        return HttpResponse("First Complete the preliminary feedback of this task")

    efb = None
    qa_list = None
    if(OngoingExecutorFeedBack.objects.filter(task=task,executor=request.user).count()>0):
        #if already partially updated list exists, fetch the feedback
        efb = OngoingExecutorFeedBack.objects.get(task=task)

    else:
        #create feedback and pass it to user for editing
        question_category = 'CEW'
        curr_time = datetime.datetime.now()
        if (task.task_category.upper() == 'SAW'):
            question_category = 'SAW'
        efb = OngoingExecutorFeedBack.objects.create(task=task, executor=request.user, approval_level=0,
                                                     created_date=curr_time)


        questions = Questions.objects.filter(employee_category='executor', task_state='ongoing',
                                             task_category=question_category).order_by('priority')

        for each in questions:
            qa = QuestionsAnswers.objects.create(task_id=task, answered_by=request.user, task_question=each)
            efb.answers.add(qa)
        efb.save()

    qa_list = efb.answers.all().order_by('task_question__priority')

    OngoingTaskQASet = modelformset_factory(form=OngoingTaskQuestionAnswer, model=QuestionsAnswers, extra=0)


    formset = None
    if(request.method == 'POST'):
        formset = OngoingTaskQASet(request.POST)
        if(formset.is_valid()):
            files = request.FILES
            for fid in files.keys():
                file = files[fid]
                print(file.name)
                file_hash_id = fid.split('_')[1]
                file_hash = request.POST[file_hash_id]
                server_url = upload_to_ftp(file, file.name)
                File.objects.create(file_name=file.name, hash=file_hash, server_loc=server_url, file_size=file.size)
            print('valid formset')


            formset.save()
    else:
        formset = OngoingTaskQASet(queryset=qa_list)

    #TODO: if all answered, increase approval level and add feedback to OngoingTaskFeedback Model
    
    context = {'task': task, 'formset':formset}

    final_submission = True
    for each in qa_list:
        if (each.answer == "" or each.answer is None):
            final_submission = False
    if (final_submission):
        context.update({'final_submission':final_submission})

    return render(request,'task_management/add_ongoing_task_executor_feedback.html',context)