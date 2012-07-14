import time
from django.db import models
from django.contrib.auth.models import User, UserManager
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, get, get_many, execute, count, countraw

class Userprofile(BaseModel):
    tweet = models.CharField(max_length=128, null=True)
    nickname = models.CharField(max_length=30, null=True)
    website = models.CharField(max_length=64, null=True) 
    company = models.CharField(max_length=64, null=True)
    location = models.CharField(max_length=64, null=True)
    resume = models.CharField(max_length=2048, null=True)
    imgurl = models.CharField(max_length=32, null=True)

    pubrepo = models.IntegerField(null=False, default=0) 
    prirepo = models.IntegerField(null=False, default=0)
    #watchrepo = models.IntegerField(null=False, default=0)
    watch = models.IntegerField(null=False, default=0)
    be_watched = models.IntegerField(null=False, default=0)
    quote = models.BigIntegerField(null=False, default=67108864)
    used_quote = models.BigIntegerField(null=False, default=0)

class Recommend(BaseModel):
    user_id = models.IntegerField(null=False, default=0)
    content = models.CharField(max_length=128, null=False)
    from_user_id = models.IntegerField(null=False, default=0)

class GsuserManager():

    @classmethod
    def get_user_by_id(self, user_id):
        return get(User, 'auth_user', user_id)

    @classmethod
    def get_user_by_name(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None 

    @classmethod
    def list_user_by_ids(self, user_ids):
        return get_many(User, 'auth_user', user_ids)

    @classmethod
    def list_userprofile_by_ids(self, user_ids):
        return get_many(Userprofile, 'gsuser_userprofile', user_ids)

    @classmethod
    def get_userprofile_by_id(self, user_id):
        return get(Userprofile, 'gsuser_userprofile', user_id)
    
    @classmethod
    def get_userprofile_by_name(self, username):
        user = self.get_user_by_name(username)
        if user is None:
            return None
        return self.get_userprofile_by_id(user.id)

    @classmethod
    def map_users(self, user_ids):
        users = self.list_user_by_ids(user_ids)
        userprofiles = self.list_userprofile_by_ids(user_ids)
        return self.merge_user_map(users, userprofiles)
        
    @classmethod
    def merge_user_map(self, users, userprofiles):
        users_map = {}
        for user in users:
            if user.id not in users_map:
                users_map[user.id] = {}
            users_map[user.id]['id'] = user.id
            users_map[user.id]['username'] = user.username
            users_map[user.id]['date_joined'] = time.mktime(user.date_joined.timetuple())
            users_map[user.id]['last_login'] = time.mktime(user.last_login.timetuple())
        for userprofile in userprofiles:
            if userprofile.id not in users_map:
                users_map[userprofile.id] = {}
            users_map[userprofile.id]['nickname'] = userprofile.nickname
            users_map[userprofile.id]['imgurl'] = userprofile.imgurl
            users_map[userprofile.id]['tweet'] = userprofile.tweet
        return users_map

    @classmethod
    def list_recommend_by_id(self, user_id, offset, row_count):
        rawsql_id = 'recommend_l_userId'
        recommends = query(Recommend, 'gsuser_recommend', user_id, rawsql_id, [user_id, offset, row_count]) 
        return list(recommends)
