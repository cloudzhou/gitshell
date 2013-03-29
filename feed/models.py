# -*- coding: utf-8 -*-  
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many, get_version, get_sqlkey
from gitshell.objectscache.da import get_raw, get_raw_many

class Feed(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0)
    repo_id = models.IntegerField(default=0)
    feed_cate = models.SmallIntegerField(default=0)
    feed_type = models.SmallIntegerField(default=0)
    relative_id = models.IntegerField(default=0)
    first_refid = models.IntegerField(default=0)
    first_refname = models.CharField(max_length=64)
    second_refid = models.IntegerField(default=0)
    second_refname = models.CharField(max_length=64)
    third_refid = models.IntegerField(default=0)
    third_refname = models.CharField(max_length=64)

    # field without database
    relative_obj = {}

    @classmethod
    def create(self, user_id, repo_id, feed_cate, feed_type, relative_id):
        feed = Feed(
            user_id = user_id,
            repo_id = repo_id,
            feed_cate = feed_cate,
            feed_type = feed_type,
            relative_id = relative_id,
        )
        return feed

class AtMessage(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    by_user_id = models.IntegerField(default=0)
    at_user_id = models.IntegerField(default=0)
    relative_id = models.IntegerField(default=0)
    at_message = models.CharField(max_length=512)

    # field without database
    relative_obj = {}

class FeedManager():

    @classmethod
    def list_atmessage_by_userId(self, user_id, offset, row_count):
        atMessages = query(AtMessage, user_id, 'atMessage_l_userId', [user_id, offset, row_count])
        return atMessages

class FEED_EVENT:

    PUSH_CID = 0,
    PUSH_COMMIT_MESSAGE = 0,
    PUSH_COMMENT_ON_COMMIT = 1,

    MERGE_CID = 1,
    MERGE_CREATE_PULL_REQUEST = 100,
    MERGE_MERGED_PULL_REQUEST = 101,
    MERGE_COMMENT_ON_PULL_REQUEST = 102,
    MERGE_REJECTED_PULL_REQUEST = 103,
    MERGE_DELETE_PULL_REQUEST = 104,

    TODO_CID = 2,
    TODO_CREATE = 200,
    TODO_DOING = 201,
    TODO_DONE = 202,
    TODO_CHANGE_PROCESS = 203,
    TODO_COMMENT_ON_TODO = 204,
    TODO_ASSIGN_TO = 205,

    ISSUES_CID = 3,
    ISSUES_CREATE = 300,
    ISSUES_STATUS_CHANGE = 301,
    ISSUES_COMMENT_ON_ISSUE = 302,

    ACTIVE_CID = 4,
    ACTIVE_STARTED_FOLLOWING = 400,
    ACTIVE_STARTED_STAR = 401,
    ACTIVE_STARTED_FORKED = 402,
    ACTIVE_JOIN_MEMBER = 403,
    ACTIVE_CREATE_PROJECT = 404,
    ACTIVE_CREATE_REPO = 405,
    ACTIVE_CREATE_BRANCH = 406,
    ACTIVE_DELETE_BRANCH = 407,

#================ Feed Event ================
"""
0 push events
    0) commit message
    1) comment on commit
1 Merge events
    100) create pull request
    101) merged pull request
    102) comment on pull request
    103) rejected pull request
    104) delete pull request
2 todo
    200) create
    201) doing
    202) done
    203) change process
    204) comment on todo
    205) assign to xxx
3 issues
    300) create
    301) status change
    302) comment on issue
4 active
    400) started following
    401) started star
    402) started forked
    403) join member
    404) create project
    405) create repo
    406) create branch
    407) delete branch
5 @ at somebody
    xxx @cloudzhou
"""
