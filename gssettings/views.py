# -*- coding: utf-8 -*-  
import base64,hashlib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from gitshell.gssettings.Form import SshpubkeyForm, ChangepasswordForm, UserprofileForm, DoSshpubkeyForm
from gitshell.keyauth.models import UserPubkey, KeyauthManager
from gitshell.objectscache.models import Count

def default(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def profile(request):
    userprofileForm = UserprofileForm()
    if request.method == 'POST':
        userprofileForm = UserprofileForm(request.POST)
    response_dictionary = {'hello_world': 'hello world', 'userprofileForm': userprofileForm}
    return render_to_response('settings/profile.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def changepassword(request):
    changepasswordForm = ChangepasswordForm()
    response_dictionary = {'hello_world': 'hello world', 'changepasswordForm': changepasswordForm}
    return render_to_response('settings/changepassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def sshpubkey(request):
    sshpubkeyForm = SshpubkeyForm()
    doSshpubkeyForm = DoSshpubkeyForm()
    error = u''
    userPubkey_all = KeyauthManager.list_userPubkey_by_user_id(request.user.id)
    print userPubkey_all
    if request.method == 'POST':
        sshpubkeyForm = SshpubkeyForm(request.POST)
        if sshpubkeyForm.is_valid():
            pubkey_name = sshpubkeyForm.cleaned_data['pubkey_name'].strip()
            pubkey = sshpubkeyForm.cleaned_data['pubkey'].strip()
            str_arr = pubkey.split()
            if len(str_arr) >= 2: 
                pubkey = ' '.join(str_arr[0:2])
                key_fingerprint = key_to_fingerprint(str_arr[1])
                if len(list(userPubkey_all)) < 11:
                    count = Count.objects.raw('SELECT 0 as id, count(1) as count FROM keyauth_userpubkey WHERE fingerprint = %s and visibly = 0', [key_fingerprint])[0]
                    if count.count < 5: 
                        userPubkey = UserPubkey() 
                        userPubkey.user_id = request.user.id
                        userPubkey.name = pubkey_name
                        userPubkey.key = pubkey
                        userPubkey.fingerprint = key_fingerprint
                        userPubkey.save()
                        return HttpResponseRedirect('/settings/sshpubkey/')
                    else:
                        error = u'您不能使用此公钥，为了防止公钥大量共享使用等原因，我们对一些公钥进行限制'
                else:
                    error = u'您最多拥有10个公钥'
        error = u'确定公钥标识非空，且公钥拷贝正确，典型公钥位置：~/.ssh/id_rsa.pub'
            
    response_dictionary = {'sshpubkeyForm': sshpubkeyForm, 'doSshpubkeyForm': doSshpubkeyForm, 'error': error,
                        'userPubkey_all': list(userPubkey_all)}
    return render_to_response('settings/sshpubkey.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

from django.db import connection, transaction
def sshpubkey_remove(request):
    doSshpubkeyForm = DoSshpubkeyForm()
    if request.method == 'POST':
        doSshpubkeyForm = DoSshpubkeyForm(request.POST)
        if doSshpubkeyForm.is_valid():
            cursor = connection.cursor()
            cursor.execute("UPDATE keyauth_userpubkey SET visibly = 1 WHERE id = %s", [doSshpubkeyForm.cleaned_data['pubkey_id']])
            transaction.commit_unless_managed()
            return HttpResponseRedirect('/settings/sshpubkey/')
    return render_to_response('settings/sshpubkey.html', {}, context_instance=RequestContext(request))

def key_to_fingerprint(pubkey):
    key = base64.b64decode(pubkey)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))    

def email(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/email.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def destroy(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/destroy.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
