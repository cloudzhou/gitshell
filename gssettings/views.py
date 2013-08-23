# -*- coding: utf-8 -*-  
import re, base64, hashlib, random
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import email_re
from django.template import RequestContext
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.settings import logger
from gitshell.viewtools.views import json_httpResponse
from gitshell.gsuser.models import Userprofile, UserEmail, GsuserManager, ThirdpartyUser, COMMON_EMAIL_DOMAIN
from gitshell.keyauth.models import UserPubkey, KeyauthManager
from gitshell.feed.models import NOTIF_TYPE, NOTIF_FQCY, FeedManager
from gitshell.gssettings.Form import SshpubkeyForm, ChangepasswordForm, UserprofileForm, DoSshpubkeyForm

@login_required
def profile(request):
    current = 'profile'
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    userprofileForm = UserprofileForm(instance = request.userprofile)
    if request.method == 'POST':
        userprofileForm = UserprofileForm(request.POST, instance = request.userprofile)
        if userprofileForm.is_valid():
            userprofileForm.save()
    response_dictionary = {'current': current, 'userprofileForm': userprofileForm, 'thirdpartyUser': thirdpartyUser}
    return render_to_response('settings/profile.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def changepassword(request):
    current = 'changepassword'
    changepasswordForm = ChangepasswordForm()
    error = u''
    if request.method == 'POST':
        changepasswordForm = ChangepasswordForm(request.POST)
        if changepasswordForm.is_valid():
            new_password = changepasswordForm.cleaned_data['password']
            request.user.set_password(new_password)
            request.user.save()
        else:
            error = u'输入正确的密码'
    response_dictionary = {'current': current, 'changepasswordForm': changepasswordForm, 'error': error}
    return render_to_response('settings/changepassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def sshpubkey(request):
    current = 'sshpubkey'
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
            
    response_dictionary = {'current': current, 'sshpubkeyForm': sshpubkeyForm, 'doSshpubkeyForm': doSshpubkeyForm, 'error': error, 'userPubkey_all': list(userPubkey_all)}
    return render_to_response('settings/sshpubkey.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def sshpubkey_remove(request):
    doSshpubkeyForm = DoSshpubkeyForm()
    if request.method == 'POST':
        doSshpubkeyForm = DoSshpubkeyForm(request.POST)
        if doSshpubkeyForm.is_valid():
            pubkey_id = doSshpubkeyForm.cleaned_data['pubkey_id']
            userPubkey = KeyauthManager.get_userpubkey_by_id(request.user.id, pubkey_id)
            if userPubkey != None:
                userPubkey.visibly = 1
                userPubkey.save()
            return HttpResponseRedirect('/settings/sshpubkey/')
    return render_to_response('settings/sshpubkey.html', {}, context_instance=RequestContext(request))

@login_required
def emails(request):
    current = 'emails'
    useremails = GsuserManager.list_useremail_by_userId(request.user.id)
    response_dictionary = {'current': current, 'useremails': useremails}
    return render_to_response('settings/emails.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@require_http_methods(["POST"])
def email_add(request):
    useremails = GsuserManager.list_useremail_by_userId(request.user.id)
    if len(useremails) >= 50:
        return json_httpResponse({'code': 500, 'message': 'hit max email count(50)'})
    email = request.POST.get('email')
    for x in useremails:
        if email == x.email:
            return json_httpResponse({'code': 500, 'message': u'添加邮箱 %s 失败，邮箱已经存在' % email})
    user = request.user
    if email and email_re.match(email):
        userEmail = UserEmail(user_id = user.id, email = email, is_verify = 0, is_primary = 0, is_public = 1)
        userEmail.save()
    return json_httpResponse({'code': 200, 'message': u'成功添加邮箱' + email})

@login_required
@require_http_methods(["POST"])
def email_primary(request, eid):
    usermail = GsuserManager.get_useremail_by_id(eid)
    if not usermail or usermail.user_id != request.user.id:
        return json_httpResponse({'code': 500, 'message': u'设置失败，没有权限'})
    useremails = GsuserManager.list_useremail_by_userId(request.user.id)
    for x in useremails:
        if usermail.id != x.id and x.is_primary == 1:
            x.is_primary = 0
            x.save()
    usermail.is_primary = 1
    usermail.save()
    return json_httpResponse({'code': 500, 'message': u'成功设置默认邮箱 %s' % usermail.email})

@login_required
@require_http_methods(["POST"])
def email_verify(request, eid):
    usermail = GsuserManager.get_useremail_by_id(eid)
    email = usermail.email
    via = ''
    if usermail and usermail.is_verify == 0 and usermail.user_id == request.user.id:
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash + '_useremail_id', eid)
        active_url = 'https://gitshell.com/settings/email/verified/%s/' % random_hash
        message = u'尊敬的gitshell用户：\n请点击下面的地址验证您在gitshell的邮箱：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
        send_mail('[gitshell]验证邮件地址', message, 'noreply@gitshell.com', [email], fail_silently=False)
        email_suffix = email.split('@')[-1]
        if email_suffix in COMMON_EMAIL_DOMAIN:
            via = COMMON_EMAIL_DOMAIN[email_suffix]
        return json_httpResponse({'code': 200, 'message': u'请尽快验证邮箱', 'via': via})
    return json_httpResponse({'code': 500, 'message': u'邮箱不对，或者没有相关权限', 'via': via})

@login_required
def email_verified(request, token):
    useremail_id = cache.get(token + '_useremail_id')
    usermail = GsuserManager.get_useremail_by_id(useremail_id)
    if usermail and usermail.is_verify == 0 and usermail.user_id == request.user.id:
        usermail.is_verify = 1
        usermail.save()
    return HttpResponseRedirect('/settings/emails/')

@login_required
@require_http_methods(["POST"])
def email_remove(request, eid):
    usermail = GsuserManager.get_useremail_by_id(eid)
    if usermail and usermail.user_id == request.user.id:
        usermail.visibly = 1
        usermail.save()
    return json_httpResponse({'code': 200, 'message': u'成功删除邮箱 ' + usermail.email})

@login_required
def notif(request):
    current = 'notif'
    notifSetting = FeedManager.get_notifsetting_by_userId(request.user.id)
    useremails = GsuserManager.list_useremail_by_userId(request.user.id)
    response_dictionary = {'current': current, 'notif_type_choice': NOTIF_TYPE.NOTIF_TYPE_CHOICE, 'notif_fqcy_choice': NOTIF_FQCY.NOTIF_FQCY_CHOICE, 'notifSetting': notifSetting, 'useremails': useremails}
    return render_to_response('settings/notif.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@require_http_methods(["POST"])
def notif_types(request):
    user = request.user
    notifSetting = FeedManager.get_notifsetting_by_userId(user.id);
    types_str = request.POST.get('types', 'all')
    types = []
    if types_str == 'all':
        notifSetting.notif_types = 'all'
    else:
        for type_str in types_str.split(','):
            if not re.match('^\d+$', type_str):
                continue
            type_ = int(type_str)
            if type_ in NOTIF_TYPE.VALUES:
                types.append(type_str);
        notifSetting.notif_types = ','.join(types)
    notifSetting.save()
    return json_httpResponse({'code': 200, 'message': u'成功修改通知 ' + types_str})

@login_required
@require_http_methods(["POST"])
def notif_fqcy(request):
    user = request.user
    notifSetting = FeedManager.get_notifsetting_by_userId(user.id);
    fqcy_str = request.POST.get('fqcy', '0')
    if re.match('^\d+$', fqcy_str):
        fqcy = int(fqcy_str)
        if fqcy in NOTIF_FQCY.VALUES:
            notifSetting.notif_fqcy = fqcy
            notifSetting.save()
    return json_httpResponse({'code': 200, 'message': u'成功修改频率 ' + fqcy_str})

@login_required
@require_http_methods(["POST"])
def notif_email(request):
    user = request.user
    notifSetting = FeedManager.get_notifsetting_by_userId(user.id);
    email = request.POST.get('email', user.email)
    if email_re.match(email):
        useremail = GsuserManager.get_useremail_by_userId_email(user.id, email)
        if useremail:
            notifSetting.email = email
            notifSetting.save()
    return json_httpResponse({'code': 200, 'message': u'成功修改邮箱 ' + email})

@login_required
def thirdparty(request):
    current = 'thirdparty'
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    response_dictionary = {'current': current, 'thirdpartyUser': thirdpartyUser}
    return render_to_response('settings/thirdparty.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def change_username_email(request):
    current = 'change_username_email'
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    response_dictionary = {'current': current, 'thirdpartyUser': thirdpartyUser}
    return render_to_response('settings/change_username_email.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def validate_email(request, token):
    current = 'validate_email'
    validate_result = 'success'
    email = cache.get(token + '_email')
    if email is not None:
        user = GsuserManager.get_user_by_email(email)
        if user is None:
            request.user.email = email
            request.userprofile.email = email
            request.user.save()
            request.userprofile.save()
        else:
            validate_result = 'user_exists'
    else:
        validate_result = 'token_expired'
    response_dictionary = {'current': current, 'validate_result': validate_result}
    return render_to_response('settings/validate_email.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def destroy(request):
    current = 'destroy'
    response_dictionary = {'current': current, 'hello_world': 'hello world'}
    return render_to_response('settings/destroy.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def key_to_fingerprint(pubkey):
    key = base64.b64decode(pubkey)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))    



