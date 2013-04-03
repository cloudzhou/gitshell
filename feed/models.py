# -*- coding: utf-8 -*-  
import re
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many, get_version, get_sqlkey
from gitshell.objectscache.da import get_raw, get_raw_many
from gitshell.gsuser.models import GsuserManager

class Feed(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0)
    repo_id = models.IntegerField(default=0)
    feed_cate = models.SmallIntegerField(default=0)
    feed_type = models.SmallIntegerField(default=0)
    relative_id = models.IntegerField(default=0, null=True)
    first_refid = models.IntegerField(default=0)
    first_refname = models.CharField(max_length=64, null=True)
    second_refid = models.IntegerField(default=0)
    second_refname = models.CharField(max_length=64, null=True)
    third_refid = models.IntegerField(default=0)
    third_refname = models.CharField(max_length=64, null=True)

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

    def is_commit_message(self):
        return self.feed_type == FEED_EVENT.PUSH_COMMIT_MESSAGE

class NotifMessage(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    notif_type = models.SmallIntegerField(default=0)
    from_user_id = models.IntegerField(default=0)
    to_user_id = models.IntegerField(default=0)
    first_refid = models.IntegerField(default=0)
    first_refname = models.CharField(max_length=64, null=True)
    second_refid = models.IntegerField(default=0)
    second_refname = models.CharField(max_length=64, null=True)
    message = models.CharField(max_length=512, null=True)
    relative_id = models.IntegerField(default=0)

    # field without database
    relative_obj = {}

    @classmethod
    def create_at(self, from_user_id, to_user_id, relative_id):
        notifMessage = NotifMessage(
            notif_type = NOTIF_TYPE.AT_ME,
            from_user_id = from_user_id,
            to_user_id = to_user_id,
            relative_id = relative_id,
        )
        return notifMessage

class FeedManager():

    @classmethod
    def list_notifmessage_by_userId(self, user_id, offset, row_count):
        notifMessages = query(NotifMessage, user_id, 'notifMessage_l_userId', [user_id, offset, row_count])
        return notifMessages

    @classmethod
    def list_feed_by_ids(self, ids):
        feeds = get_many(Feed, ids)
        return feeds

    @classmethod
    def notif_commit_at(self, from_user_id, commitHistory_id, commit_message):
        at_name_list = FeedUtils.list_atname(commit_message)
        user_unread_message_dict = {}

        for at_name in at_name_list:
            at_user = GsuserManager.get_user_by_name(at_name)
            if at_user is not None:
                to_user_id = at_user.id
                notifMessage = NotifMessage.create_at(from_user_id, to_user_id, commitHistory_id)
                notifMessage.save()
                if to_user_id not in user_unread_message_dict:
                    user_unread_message_dict[to_user_id] = 0
                user_unread_message_dict[to_user_id] = user_unread_message_dict[to_user_id] + 1

        print user_unread_message_dict
        for to_user_id, unread_message in user_unread_message_dict.items():
            at_userprofile = GsuserManager.get_userprofile_by_id(to_user_id)
            print at_userprofile.unread_message
            at_userprofile.unread_message = at_userprofile.unread_message + unread_message
            print at_userprofile.unread_message
            at_userprofile.save()

class FeedUtils():

    @classmethod
    def list_atname(self, atmessage):
        wc = re.compile(r"\w+")
        at_name_list = []
        at_index_list = []
        is_has_at = False
        i = 0
        for x in atmessage:
            if x == '@':
                if is_has_at:
                    at_index_list.append(i)
                is_has_at = True
                at_index_list.append(i)
            elif not wc.match(x):
                if is_has_at:
                    at_index_list.append(i)
                    is_has_at = False
            if len(at_index_list) > 20:
                break
            i = i + 1
        if is_has_at:
            at_index_list.append(i)
        j = 0
        while j < len(at_index_list)/2:
            begin = at_index_list[j*2] + 1
            end = at_index_list[j*2 + 1]
            if begin < end:
                at_name_list.append(atmessage[begin : end])
            j = j + 1
        return at_name_list


class NOTIF_TYPE:

    AT_ME = 0
    COMMENT_ME = 1
    MESSAGE = 2
    
class FEED_EVENT:

    PUSH_CID = 0
    PUSH_COMMIT_MESSAGE = 0
    PUSH_COMMENT_ON_COMMIT = 1

    MERGE_CID = 1
    MERGE_CREATE_PULL_REQUEST = 100
    MERGE_MERGED_PULL_REQUEST = 101
    MERGE_COMMENT_ON_PULL_REQUEST = 102
    MERGE_REJECTED_PULL_REQUEST = 103
    MERGE_DELETE_PULL_REQUEST = 104

    TODO_CID = 2
    TODO_CREATE = 200
    TODO_DOING = 201
    TODO_DONE = 202
    TODO_CHANGE_PROCESS = 203
    TODO_COMMENT_ON_TODO = 204
    TODO_ASSIGN_TO = 205

    ISSUES_CID = 3
    ISSUES_CREATE = 300
    ISSUES_STATUS_CHANGE = 301
    ISSUES_COMMENT_ON_ISSUE = 302

    ACTIVE_CID = 4
    ACTIVE_STARTED_FOLLOWING = 400
    ACTIVE_STARTED_STAR = 401
    ACTIVE_STARTED_FORKED = 402
    ACTIVE_JOIN_MEMBER = 403
    ACTIVE_CREATE_PROJECT = 404
    ACTIVE_CREATE_REPO = 405
    ACTIVE_CREATE_BRANCH = 406
    ACTIVE_DELETE_BRANCH = 407

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
