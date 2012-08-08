# -*- coding: utf-8 -*-  
import base64, hashlib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from gitshell.gssettings.Form import SshpubkeyForm, ChangepasswordForm, UserprofileForm, DoSshpubkeyForm
from gitshell.keyauth.models import UserPubkey, KeyauthManager
from gitshell.gsuser.models import Userprofile, GsuserManager

@login_required
def profile(request):
    userprofileForm = UserprofileForm(instance = request.userprofile)
    if request.method == 'POST':
        userprofileForm = UserprofileForm(request.POST, instance = request.userprofile)
        if userprofileForm.is_valid():
            userprofileForm.save()
    response_dictionary = {'userprofileForm': userprofileForm}
    return render_to_response('settings/profile.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def changepassword(request):
    changepasswordForm = ChangepasswordForm()
    error = u''
    if request.method == 'POST':
        changepasswordForm = ChangepasswordForm(request.POST)
        if changepasswordForm.is_valid():
            old_password = changepasswordForm.cleaned_data['old_password']
            new_password = changepasswordForm.cleaned_data['password']
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()
                return HttpResponseRedirect('/home/')
            else:
                error = u'确定原密码正确？'
        else:
            error = u'输入正确的密码'
    response_dictionary = {'changepasswordForm': changepasswordForm, 'error': error}
    return render_to_response('settings/changepassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def sshpubkey(request):
    sshpubkeyForm = SshpubkeyForm()
    doSshpubkeyForm = DoSshpubkeyForm()
    error = u''
    userPubkey_all = KeyauthManager.list_userpubkey_by_userId(request.user.id)
    if request.method == 'POST':
        sshpubkeyForm = SshpubkeyForm(request.POST)
        if sshpubkeyForm.is_valid():
            pubkey_name = sshpubkeyForm.cleaned_data['pubkey_name'].strip()
            pubkey = sshpubkeyForm.cleaned_data['pubkey'].strip()
            str_arr = pubkey.split()
            if len(str_arr) >= 2: 
                pubkey = ' '.join(str_arr[0:2])
                fingerprint = key_to_fingerprint(str_arr[1])
                if len(list(userPubkey_all)) < 11:
                    count = KeyauthManager.count_userpubkey_by_fingerprint(fingerprint)
                    if count < 5: 
                        userPubkey = UserPubkey() 
                        userPubkey.user_id = request.user.id
                        userPubkey.name = pubkey_name
                        userPubkey.key = pubkey
                        userPubkey.fingerprint = fingerprint
                        userPubkey.save()
                        return HttpResponseRedirect('/settings/sshpubkey/')
                    else:
                        error = u'您不能使用此公钥，为了防止公钥大量共享使用等原因，我们对一些公钥进行限制'
                else:
                    error = u'您最多拥有10个公钥'
        else:
            error = u'确定公钥标识非空，且公钥拷贝正确，典型公钥位置：~/.ssh/id_rsa.pub'
            
    response_dictionary = {'sshpubkeyForm': sshpubkeyForm, 'doSshpubkeyForm': doSshpubkeyForm, 'error': error,
                        'userPubkey_all': list(userPubkey_all)}
    return render_to_response('settings/sshpubkey.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def sshpubkey_remove(request):
    doSshpubkeyForm = DoSshpubkeyForm()
    if request.method == 'POST':
        doSshpubkeyForm = DoSshpubkeyForm(request.POST)
        if doSshpubkeyForm.is_valid():
            KeyauthManager.update_userpubkey_by_id(doSshpubkeyForm.cleaned_data['pubkey_id'])
            return HttpResponseRedirect('/settings/sshpubkey/')
    return render_to_response('settings/sshpubkey.html', {}, context_instance=RequestContext(request))

@login_required
def email(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/email.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def repo(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def destroy(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/destroy.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def key_to_fingerprint(pubkey):
    key = base64.b64decode(pubkey)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))    

