import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
import base64, hashlib
from django.db import IntegrityError
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from gitshell.gsuser.models import Userprofile, GsuserManager, ThirdpartyUser, COMMON_EMAIL_DOMAIN
from gitshell.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

def github_oauth_access_token(code):
    githup_connection = None
    try:
        githup_connection = httplib.HTTPSConnection('github.com', 443, timeout=10)
        params = urllib.urlencode({'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        githup_connection.request("POST", "/login/oauth/access_token", params, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            response = json.loads(json_str)
            access_token = str(response['access_token'])
            return access_token
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return '' 

def github_get_thirdpartyUser(access_token):
    githup_connection = None
    try:
        thirdpartyUser = ThirdpartyUser()
        githup_connection = httplib.HTTPSConnection('api.github.com', 443, timeout=10)
        headers = {"Host": "api.github.com", "Accept": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"}
        githup_connection.request("GET", "/user?access_token=" + access_token, {}, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            response = json.loads(json_str)
            if 'login' in response:
                thirdpartyUser.tp_username = response['login']
            if 'id' in response:
                thirdpartyUser.tp_id = response['id']
            if 'email' in response:
                thirdpartyUser.tp_email = response['email']
            thirdpartyUser.init = 0
            thirdpartyUser.access_token = access_token
            thirdpartyUser.user_type = ThirdpartyUser.GITHUB
            return thirdpartyUser
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return '' 
    
def github_authenticate(thirdpartyUser):
    tp_id, tp_username, tp_email = thirdpartyUser.tp_id, thirdpartyUser.tp_username, thirdpartyUser.tp_email
    thirdpartyUser_find = GsuserManager.get_thirdpartyUser_by_type_tpId(ThirdpartyUser.GITHUB, tp_id)
    if thirdpartyUser_find is not None:
        if thirdpartyUser_find.access_token != thirdpartyUser.access_token:
            thirdpartyUser_find.access_token = thirdpartyUser.access_token
            thirdpartyUser_find.save()
        user_id = thirdpartyUser_find.id
        user = GsuserManager.get_user_by_id(user_id)
        return user
    username = __get_uniq_username(tp_username)
    email = __get_uniq_email(tp_email)
    password = __get_random_password()
    if username is None or email is None or password is None:
        return None
    create_user = None
    try:
        create_user = User.objects.create_user(username, email, password)
        if create_user is not None and create_user.is_active:
            userprofile = Userprofile(username = create_user.username, email = create_user.email, imgurl = hashlib.md5(create_user.email.lower()).hexdigest())
            userprofile.id = create_user.id
            userprofile.save()
            if username == tp_username and email == tp_email:
                thirdpartyUser.init = 1
            thirdpartyUser.user_type = ThirdpartyUser.GITHUB
            thirdpartyUser.id = create_user.id
            thirdpartyUser.save()
    except IntegrityError:
        print 'user IntegrityError'
    return create_user

def github_list_repo(access_token):
    try:
        pass
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return '' 

def __get_uniq_username(tp_username):
    if tp_username is not None:
        user = GsuserManager.get_user_by_name(tp_username)
        if user is None:
            return tp_username
    for i in range(0, 1000):
        random_username = '%8x' % random.getrandbits(64)
        user = GsuserManager.get_user_by_name(random_username)
        if user is None:
            return random_username
    return None

def __get_uniq_email(tp_email):
    if tp_email is not None:
        user = GsuserManager.get_user_by_email(tp_email)
        if user is None:
            return tp_email
    for i in range(0, 1000):
        random_email = ('%8x' % random.getrandbits(64)) + '@example.com'
        user = GsuserManager.get_user_by_email(random_email)
        if user is None:
            return random_email
    return None

def __get_random_password():
    return '%8x' % random.getrandbits(64)
