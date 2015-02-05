from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from actstream.models import model_stream

from sprints.models import Sprint
from accounts.models import RoleAssigned

__author__ = 'Derek Stegelman'
__date__ = '10/17/12'


def homepage(request):
    if request.user.is_authenticated():

        context = {'sprints': Sprint.objects.all()}
        teams = RoleAssigned.objects.filter(user=request.user)
        context['teams'] = teams
        context['model_stream'] = model_stream(request.user)[:25]

        return render(request, 'core/homepage.html', context)
    else:
        return render(request, 'index.html')