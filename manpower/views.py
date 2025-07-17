from django.shortcuts import render, redirect


# Create your views here.

def homepage(request):
    if (request.user.is_anonymous):
        return redirect('/')

    if (request.user.profile.grade > 25):
        return redirect('/task_list_ru')
    return render(request,'manpower/manpower_base.html')