import time
from django.db import models
from django.contrib.auth.models import User, UserManager
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, query_first, get, get_many, execute, count, countraw

class Userprofile(BaseModel):
    username = models.CharField(max_length=30, null=True)
    email = models.CharField(max_length=75, null=True)
    tweet = models.CharField(max_length=128, null=True)
    nickname = models.CharField(max_length=30, null=True)
    website = models.CharField(max_length=64, null=True) 
    company = models.CharField(max_length=64, null=True)
    location = models.CharField(max_length=64, null=True)
    resume = models.CharField(max_length=2048, null=True)
    imgurl = models.CharField(max_length=32, null=True)

    pubrepo = models.IntegerField(default=0, null=False) 
    prirepo = models.IntegerField(default=0, null=False)
    watchrepo = models.IntegerField(default=0, null=False)
    watch = models.IntegerField(default=0, null=False)
    be_watched = models.IntegerField(default=0, null=False)
    quote = models.BigIntegerField(default=536870912, null=False)
    used_quote = models.BigIntegerField(default=0, null=False)

    unread_message = models.IntegerField(default=0, null=False)

    # what about joined_team_count
    is_join_team = models.IntegerField(default=0, null=False)
    current_user_id = models.IntegerField(default=0, null=False)
    is_team_account = models.IntegerField(default=0, null=False)
    creator_user_id = models.IntegerField(default=0, null=False)

    def current_user(self):
        if self._current_user and self._current_user.id == self.current_user_id:
            return self._current_user
        self._current_user = GsuserManager.get_userprofile_by_id(self.current_user_id)
        return self._current_user

    def get_total_repo(self):
        return self.prirepo + self.pubrepo

    def get_used_repo_percent(self):
        return (self.get_total_repo()/100.0)*100.0;

    def get_used_quote_percent(self):
        return (self.used_quote*1.0/self.quote)*100.0;

    def get_readable_used_quote(self):
        return self._get_readable_du(self.used_quote)

    def get_readable_quote(self):
        return self._get_readable_du(self.quote)

    def _get_readable_du(self, quote):
        if quote < 1024:
            return str(quote) + 'b'
        if quote < 1048576:
            return str(quote/1024) + 'kb'
        if quote < 1073741824:
            return str(quote/1048576) + 'mb'
        return str(quote/1073741824) + 'g'

   ### auth_user filed ###
    _current_user = None
    date_joined = 0
    last_login = 0

class ThirdpartyUser(BaseModel):
    user_type = models.IntegerField(default=0, null=True)
    tp_id = models.IntegerField(default=0, null=True)
    tp_username = models.CharField(max_length=30, null=True)
    tp_email = models.CharField(max_length=75, null=True)
    identity = models.CharField(max_length=30, null=True)
    access_token = models.CharField(max_length=40, null=True)
    init = models.IntegerField(default=0, null=True)

    github_user_info = {}
    GITHUB = 1
    GOOGLE = 2

class UserViaRef(BaseModel):
    username = models.CharField(max_length=30, null=True)
    email = models.CharField(max_length=75, null=True)
    ref_type = models.IntegerField(default=0, null=True)
    ref_hash = models.CharField(max_length=40, null=True)
    ref_message = models.CharField(max_length=256, null=True)
    first_refid = models.IntegerField(default=0)
    first_refname = models.CharField(max_length=64, null=True)
    second_refid = models.IntegerField(default=0)
    second_refname = models.CharField(max_length=64, null=True)
    third_refid = models.IntegerField(default=0)
    third_refname = models.CharField(max_length=64, null=True)

class UserEmail(BaseModel):
    user_id = models.IntegerField(default=0, null=False)
    email = models.CharField(max_length=75, null=True)
    is_verify = models.IntegerField(default=0, null=True)
    is_primary = models.IntegerField(default=0, null=True)
    is_public = models.IntegerField(default=0, null=True)

class Recommend(BaseModel):
    user_id = models.IntegerField(default=0, null=False)
    content = models.CharField(max_length=128, null=False)
    from_user_id = models.IntegerField(default=0, null=False)

    def to_recommend_vo(self, users_map):
        recommend_vo = {}
        recommend_vo['id'] = self.id
        recommend_vo['content'] = self.content
        if self.from_user_id in users_map:
            recommend_vo['username'] = users_map[self.from_user_id]['username']
            recommend_vo['imgurl'] = users_map[self.from_user_id]['imgurl']
            recommend_vo['tweet'] = users_map[self.from_user_id]['tweet']
        return recommend_vo

class GsuserManager():

    @classmethod
    def get_user_by_id(self, user_id):
        return get(User, user_id)

    @classmethod
    def get_user_by_name(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None 

    @classmethod
    def get_user_by_email(self, email):
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            return None 

    @classmethod
    def list_user_by_ids(self, user_ids):
        return get_many(User, user_ids)

    @classmethod
    def list_userprofile_by_ids(self, user_ids):
        return get_many(Userprofile, user_ids)

    @classmethod
    def get_userprofile_by_id(self, user_id):
        return get(Userprofile, user_id)
    
    @classmethod
    def get_userprofile_by_email(self, email):
        try:
            userprofile = Userprofile.objects.get(email=email)
            return userprofile
        except Userprofile.DoesNotExist:
            return None 

    @classmethod
    def get_userprofile_by_name(self, username):
        user = self.get_user_by_name(username)
        if user is None:
            return None
        return self.get_userprofile_by_id(user.id)

    @classmethod
    def get_thirdpartyUser_by_id(self, id):
        return get(ThirdpartyUser, id)

    @classmethod
    def get_thirdpartyUser_by_type_tpId(self, user_type, tp_id):
        thirdpartyUser = query_first(ThirdpartyUser, user_type, 'thirdpartyuser_s_userType_tpId', [user_type, tp_id]) 
        return thirdpartyUser

    @classmethod
    def handle_user_via_refhash(self, user, ref_hash):
        userViaRefs = UserViaRef.objects.filter(ref_hash=ref_hash)[0:1]
        if len(userViaRefs) == 0:
            return
        userViaRef = userViaRefs[0]
        # ref user by add team member via email
        if userViaRef.ref_type == 0:
            teamUser = GsuserManager.get_user_by_id(userViaRef.first_refid)
            userprofile = GsuserManager.get_userprofile_by_id(user.id)
            TeamManager.add_teamMember_by_userprofile(teamUser, userprofile)
        # ref user by add repo member via email
        elif userViaRef.ref_type == 1:
            RepoManager.add_member(userViaRef.second_refid, user.username)
        elif userViaRef.ref_type == 2:
            pass

    @classmethod
    def list_useremail_by_userId(self, user_id):
        user = GsuserManager.get_userprofile_by_id(user_id)
        userEmails = query(UserEmail, user_id, 'useremail_l_userId', [user_id]) 
        if len(userEmails) == 0:
            userEmail = UserEmail(user_id = user.id, email = user.email, is_verify = 1, is_primary = 1, is_public = 1)
            userEmail.save()
            userEmails.append(userEmail)
        return userEmails

    @classmethod
    def get_useremail_by_userId_email(self, user_id, email):
        userEmail = query_first(UserEmail, user_id, 'useremail_s_userId_email', [user_id, email]) 
        return userEmail

    @classmethod
    def get_useremail_by_id(self, id):
        return get(UserEmail, id)

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
    def list_recommend_by_userid(self, user_id, offset, row_count):
        rawsql_id = 'recommend_l_userId'
        recommends = query(Recommend, user_id, rawsql_id, [user_id, offset, row_count]) 
        return recommends

    @classmethod
    def get_recommend_by_id(self, rid):
        return get(Recommend, rid)

COMMON_EMAIL_DOMAIN = {
    'qq.com': 'mail.qq.com',
    '163.com': 'mail.163.com',
    '126.com': '126.com',
    'sina.com': 'mail.sina.com.cn',
    'yahoo.com.cn': 'cn.mail.yahoo.com',
    'hotmail.com': 'hotmail.com',
    'gmail.com': 'gmail.com',
    'sohu.com': 'mail.sohu.com',
    'yahoo.cn': 'cn.mail.yahoo.com',
    'tom.com': 'mail.tom.com',
    'live.com': 'mail.live.com',
}

