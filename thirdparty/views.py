import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
import base64, hashlib
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from gitshell.gsuser.models import Userprofile, GsuserManager, ThirdpartyUser, COMMON_EMAIL_DOMAIN
from gitshell.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

def github_oauth_access_token(code):
    try:
        githup_connection = httplib.HTTPSConnection('github.com', 443, timeout=10)
        params = urllib.urlencode({'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        githup_connection.request("POST", "/login/oauth/access_token", params, headers)
        response = githup_connection.getresponse()
        print response.status
        if response.status == 200:
            json_str = response.read()
            print json_str
            response = json.loads(json_str)
            access_token = str(response['access_token'])
            return access_token
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return '' 

def github_get_thirdpartyUser(access_token):
    try:
        thirdpartyUser = ThirdpartyUser()
        githup_connection = httplib.HTTPSConnection('api.github.com', 443, timeout=10)
        headers = {"Host": "api.github.com", "Accept": "application/json"}
        githup_connection.request("GET", "/user?access_token=" + access_token, {}, headers)
        response = githup_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            response = json.loads(json_str)
            if 'login' in response:
                thirdpartyUser.tp_username = response['login']
            if 'id' in response:
                thirdpartyUser.tp_user_id = response['id']
            if 'email' in response:
                thirdpartyUser.tp_email = response['email']
            thirdpartyUser.user_type = ThirdpartyUser.GITHUB
            return thirdpartyUser
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if githup_connection: githup_connection.close()
    return '' 
    
def github_authenticate(thirdpartyUser):
    tp_user_id, tp_username, tp_email = thirdpartyUser.tp_user_id, thirdpartyUser.tp_username, thirdpartyUser.tp_email
    thirdpartyUser_find = GsuserManager.get_thirdpartyUser_by_type_id(ThirdpartyUser.GITHUB, tp_user_id)
    if thirdpartyUser_find is not None:
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
        if user is not None and create_user.is_active:
            userprofile = Userprofile( username = user.username, email = user.email, imgurl = hashlib.md5(user.email.lower()).hexdigest())
            userprofile.id = user.id
            userprofile.save()
            thirdpartyUser = ThirdpartyUser(user_type = ThirdpartyUser.GITHUB, tp_user_id = tp_user_id, tp_username = username, tp_email = email)
            thirdpartyUser.id = user.id
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
    user = GsuserManager.get_user_by_email(tp_email)
    if user is None:
        return tp_email
    for i in range(0, 1000):
        random_email = '%8x' % random.getrandbits(64)
        user = GsuserManager.get_user_by_email(random_email)
        if user is None:
            return random_email
    return None

def __get_random_password():
    return '%8x' % random.getrandbits(64)
