# -*- coding: utf-8 -*-  
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from gitshell.gsuser.Forms import SkillsForm

def skills(request):
    skillsForm = SkillsForm()
    response_dictionary = {'ii': range(0, 5), 'jj': range(0, 3), 'kk': range(0, 10), 'skillsForm': skillsForm}
    return render_to_response('skills/skills.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
