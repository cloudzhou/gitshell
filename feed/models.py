# -*- coding: utf-8 -*-  
import re, time
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, query_first, queryraw, execute, count, get, get_many, get_version, get_sqlkey
from gitshell.objectscache.da import get_raw, get_raw_many
from gitshell.gsuser.models import GsuserManager
from gitshell.repo.models import RepoManager, PullRequest, PULL_STATUS
from gitshell.feed.feed import FeedAction

class Feed(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    user_id = models.IntegerField(default=0)
    repo_id = models.IntegerField(default=0)
    auth_type = models.SmallIntegerField(default=0)
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

    @classmethod
    def create_push_commit(self, user_id, repo_id, relative_id):
        return self.create(user_id, repo_id, FEED_CATE.PUSH, FEED_TYPE.PUSH_COMMIT_MESSAGE, relative_id)

    def is_commit_message(self):
        return self.feed_type == FEED_TYPE.PUSH_COMMIT_MESSAGE

    def is_issue_event(self):
        return self.feed_type == FEED_TYPE.ISSUES_CREATE or self.feed_type == FEED_TYPE.ISSUES_UPDATE or self.feed_type == FEED_TYPE.ISSUES_STATUS_CHANGE

    def is_pull_event(self):
        return self.feed_type >= FEED_TYPE.MERGE_CREATE_PULL_REQUEST and self.feed_type <= FEED_TYPE.MERGE_COMMENT_ON_PULL_REQUEST

class NotifMessage(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    notif_cate = models.SmallIntegerField(default=0)
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
    relative_name = ""
    relative_obj = {}

    @classmethod
    def create(self, notif_cate, notif_type, from_user_id, to_user_id, relative_id):
        notifMessage = NotifMessage(
            notif_cate = notif_cate,
            notif_type = notif_type,
            from_user_id = from_user_id,
            to_user_id = to_user_id,
            relative_id = relative_id,
        )
        return notifMessage

    @classmethod
    def create_at_commit(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_COMMIT, from_user_id, to_user_id, relative_id)

    @classmethod
    def create_at_issue(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_ISSUE, from_user_id, to_user_id, relative_id)

    @classmethod
    def create_at_issue_comment(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_ISSUE_COMMENT, from_user_id, to_user_id, relative_id)

    def is_at_commit(self):
        return self.notif_type == NOTIF_TYPE.AT_COMMIT
    def is_at_issue(self):
        return self.notif_type == NOTIF_TYPE.AT_ISSUE
    def is_at_issue_comment(self):
        return self.notif_type == NOTIF_TYPE.AT_ISSUE_COMMENT
    def is_pull_request_cate(self):
        return self.notif_cate == NOTIF_CATE.MERGE

class FeedManager():

    @classmethod
    def list_notifmessage_by_userId(self, user_id, offset, row_count):
        notifMessages = query(NotifMessage, user_id, 'notifMessage_l_userId', [user_id, offset, row_count])
        for notifMessage in notifMessages:
            relative_user = GsuserManager.get_user_by_id(notifMessage.from_user_id)
            if relative_user is not None:
                notifMessage.relative_name = relative_user.username
            if notifMessage.is_at_commit():
                commitHistory = RepoManager.get_commit_by_id(notifMessage.relative_id)
                notifMessage.relative_obj = commitHistory
            elif notifMessage.is_at_issue():
                issues = RepoManager.get_issues_by_id(notifMessage.relative_id)
                if issues is not None:
                    repo = RepoManager.get_repo_by_id(issues.repo_id)
                    if repo is not None:
                        issues.username = repo.get_repo_username()
                        issues.reponame = repo.name
                notifMessage.relative_obj = issues
            elif notifMessage.is_at_issue_comment():
                issues_comment = RepoManager.get_issues_comment(notifMessage.relative_id)
                issues = RepoManager.get_issues_by_id(issues_comment.issues_id)
                if issues is not None:
                    repo = RepoManager.get_repo_by_id(issues.repo_id)
                    if repo is not None:
                        issues_comment.username = repo.get_repo_username()
                        issues_comment.reponame = repo.name
                notifMessage.relative_obj = issues_comment
            elif notifMessage.is_pull_request_cate():
                pullRequest = RepoManager.get_pullRequest_by_id(notifMessage.relative_id)
                notifMessage.relative_obj = pullRequest
        return notifMessages

    @classmethod
    def get_notifmessage_by_userId_relativeId(self, user_id, relative_id):
        notifMessage = query_first(NotifMessage, user_id, 'notifMessage_s_userId_relativeId', [user_id, relative_id])
        return notifMessage

    @classmethod
    def list_feed_by_ids(self, ids):
        feeds = get_many(Feed, ids)
        return feeds

    @classmethod
    def feed_issue_change(self, user, repo, orgi_issue, current_issue_id):
        current_issue = RepoManager.get_issues_by_id(current_issue_id)
        if current_issue is None:
            return
        feed_cate = FEED_CATE.ISSUES
        message = ''
        if orgi_issue is None and current_issue is not None:
            feed_type = FEED_TYPE.ISSUES_CREATE
            message = 'create issue'
        if orgi_issue is not None and (orgi_issue.subject != current_issue.subject or orgi_issue.content != current_issue.content or orgi_issue.category != current_issue.category):
            feed_type = FEED_TYPE.ISSUES_UPDATE
            message = 'update issue'
        # status update
        status_changes = []
        if orgi_issue is not None:
            if orgi_issue.tracker != current_issue.tracker:
                status_changes.append('跟踪: ' + ISSUE_ATTR_DICT.TRACKER[current_issue.tracker])
            if orgi_issue.status != current_issue.status:
                status_changes.append('状态: ' + ISSUE_ATTR_DICT.STATUS[current_issue.status])
            if orgi_issue.assigned != current_issue.assigned:
                assigned_user = GsuserManager.get_user_by_id(current_issue.assigned)
                if assigned_user is not None:
                    status_changes.append('指派给: @' + assigned_user.username)
            if orgi_issue.priority != current_issue.priority:
                status_changes.append('优先级: ' + ISSUE_ATTR_DICT.PRIORITY[current_issue.priority])
            
            if len(status_changes) > 0:
                message = ', '.join(status_changes)
                feed_type = FEED_TYPE.ISSUES_STATUS_CHANGE

        if message != '':
            feed = Feed.create(user.id, repo.id, feed_cate, feed_type, current_issue.id)
            # TODO
            feed.first_refname = message
            feed.save()
            feedAction = FeedAction()
            timestamp = float(time.mktime(feed.create_time.timetuple()))
            feedAction.add_repo_feed(repo.id, timestamp, feed.id)
            if repo.auth_type == 2:
                feedAction.add_pri_user_feed(user.id, timestamp, feed.id)
            else:
                feedAction.add_pub_user_feed(user.id, timestamp, feed.id)

    @classmethod
    def feed_pull_change(self, pullRequest, pullStatus):
        feed_cate = FEED_CATE.MERGE
        feed_type = FEED_TYPE.MERGE_CREATE_PULL_REQUEST
        timestamp = float(time.mktime(pullRequest.modify_time.timetuple()))
        repo = pullRequest.desc_repo
        user = pullRequest.merge_user
        if pullStatus == PULL_STATUS.NEW:
            user = pullRequest.pull_user
            feed_type = FEED_TYPE.MERGE_CREATE_PULL_REQUEST
        elif pullStatus == PULL_STATUS.MERGED_FAILED:
            feed_type = FEED_TYPE.MERGE_MERGED_FAILED_PULL_REQUEST
        elif pullStatus == PULL_STATUS.MERGED:
            feed_type = FEED_TYPE.MERGE_MERGED_PULL_REQUEST
        elif pullStatus == PULL_STATUS.REJECTED:
            feed_type = NOTIF_TYPE.MERGE_REJECTED_PULL_REQUEST
        elif pullStatus == PULL_STATUS.CLOSE:
            feed_type = NOTIF_TYPE.MERGE_CLOSE_PULL_REQUEST
        feed = Feed.create(user.id, repo.id, feed_cate, feed_type, pullRequest.id)
        feed.save()
        feedAction = FeedAction()
        feedAction.add_repo_feed(repo.id, timestamp, feed.id)
        if repo.auth_type == 2:
            feedAction.add_pri_user_feed(user.id, timestamp, feed.id)
        else:
            feedAction.add_pub_user_feed(user.id, timestamp, feed.id)

    @classmethod
    def notif_at(self, feed_type, from_user_id, relative_id, message):
        at_name_list = FeedUtils.list_atname(message)
        user_unread_message_dict = {}

        for at_name in at_name_list:
            at_user = GsuserManager.get_user_by_name(at_name)
            if at_user is not None:
                to_user_id = at_user.id
                notifMessage = None
                # disable duplicate notify
                exists_notifMessage = self.get_notifmessage_by_userId_relativeId(to_user_id, relative_id)
                if exists_notifMessage is not None:
                    continue
                if feed_type == NOTIF_TYPE.AT_COMMIT:
                    notifMessage = NotifMessage.create_at_commit(from_user_id, to_user_id, relative_id)
                elif feed_type == NOTIF_TYPE.AT_ISSUE:
                    notifMessage = NotifMessage.create_at_issue(from_user_id, to_user_id, relative_id)
                elif feed_type == NOTIF_TYPE.AT_ISSUE_COMMENT:
                    notifMessage = NotifMessage.create_at_issue_comment(from_user_id, to_user_id, relative_id)
                if notifMessage is None:
                    continue
                notifMessage.save()
                if to_user_id not in user_unread_message_dict:
                    user_unread_message_dict[to_user_id] = 0
                user_unread_message_dict[to_user_id] = user_unread_message_dict[to_user_id] + 1

        for to_user_id, unread_message in user_unread_message_dict.items():
            at_userprofile = GsuserManager.get_userprofile_by_id(to_user_id)
            at_userprofile.unread_message = at_userprofile.unread_message + unread_message
            at_userprofile.save()

    @classmethod
    def notif_commit_at(self, from_user_id, commitHistory_id, commit_message):
        self.notif_at(NOTIF_TYPE.AT_COMMIT, from_user_id, commitHistory_id, commit_message)

    @classmethod
    def notif_issue_at(self, from_user_id, issue_id, issue_message):
        self.notif_at(NOTIF_TYPE.AT_ISSUE, from_user_id, issue_id, issue_message)

    @classmethod
    def notif_issue_comment_at(self, from_user_id, issue_comment_id, issue_comment_message):
        self.notif_at(NOTIF_TYPE.AT_ISSUE_COMMENT, from_user_id, issue_comment_id, issue_comment_message)

    @classmethod
    def notif_pull_request_status(self, pullRequest, pullStatus):
        notfi_type = NOTIF_TYPE.MERGE_CREATE_PULL_REQUEST
        message = ''
        if pullStatus == PULL_STATUS.NEW:
            message = 'created'
            merge_user_profile = GsuserManager.get_userprofile_by_id(pullRequest.merge_user_id)
            if merge_user_profile is not None:
                notifMessage = NotifMessage.create(NOTIF_CATE.MERGE, NOTIF_TYPE.MERGE_CREATE_PULL_REQUEST, pullRequest.pull_user_id, pullRequest.merge_user_id, pullRequest.id)
                notifMessage.message = message
                notifMessage.save()
            merge_user_profile.unread_message = merge_user_profile.unread_message + 1
            merge_user_profile.save()
            return
        if pullStatus == PULL_STATUS.MERGED_FAILED:
            notif_type = NOTIF_TYPE.MERGE_MERGED_FAILED_PULL_REQUEST
            message = 'merge failed'
        elif pullStatus == PULL_STATUS.MERGED:
            notif_type = NOTIF_TYPE.MERGE_MERGED_PULL_REQUEST
            message = 'merged'
        elif pullStatus == PULL_STATUS.REJECTED:
            notif_type = NOTIF_TYPE.MERGE_REJECTED_PULL_REQUEST
            message = 'rejected'
        elif pullStatus == PULL_STATUS.CLOSE:
            notif_type = NOTIF_TYPE.MERGE_CLOSE_PULL_REQUEST
            message = 'closed'
        pull_user_profile = GsuserManager.get_userprofile_by_id(pullRequest.pull_user_id)
        if pull_user_profile is not None:
            notifMessage = NotifMessage.create(NOTIF_CATE.MERGE, notif_type, pullRequest.merge_user_id, pullRequest.pull_user_id, pullRequest.id)
            notifMessage.message = message
            notifMessage.save()
        pull_user_profile.unread_message = pull_user_profile.unread_message + 1
        pull_user_profile.save()

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

class ISSUE_ATTR_DICT:

    TRACKER = { 
        1: '缺陷',
        2: '功能',
        3: '支持',
    }
    STATUS = {
        1: '新建',
        2: '已指派',
        3: '进行中',
        4: '已解决',
        5: '已关闭',
        6: '已拒绝',
    }
    PRIORITY = {
        1: '紧急',
        2: '高',
        3: '普通',
        4: '低',
    }

class NOTIF_CATE:

    AT = 0
    MERGE = 1

class NOTIF_TYPE:

    AT_COMMIT = 0
    AT_ISSUE = 1
    AT_ISSUE_COMMENT = 2

    MERGE_CREATE_PULL_REQUEST = 100
    MERGE_MERGED_PULL_REQUEST = 101
    MERGE_MERGED_FAILED_PULL_REQUEST = 102
    MERGE_REJECTED_PULL_REQUEST = 103
    MERGE_CLOSE_PULL_REQUEST = 104
    MERGE_COMMENT_ON_PULL_REQUEST = 105
    
class FEED_CATE:

    PUSH = 0
    MERGE = 1
    TODO = 2
    ISSUES = 3
    ACTIVE = 4

class FEED_TYPE:

    PUSH_COMMIT_MESSAGE = 0
    PUSH_COMMENT_ON_COMMIT = 1

    MERGE_CREATE_PULL_REQUEST = 100
    MERGE_MERGED_PULL_REQUEST = 101
    MERGE_MERGED_FAILED_PULL_REQUEST = 102
    MERGE_REJECTED_PULL_REQUEST = 103
    MERGE_CLOSE_PULL_REQUEST = 104
    MERGE_COMMENT_ON_PULL_REQUEST = 105

    TODO_CREATE = 200
    TODO_DOING = 201
    TODO_DONE = 202
    TODO_CHANGE_PROCESS = 203
    TODO_COMMENT_ON_TODO = 204
    TODO_ASSIGN_TO = 205

    ISSUES_CREATE = 300
    ISSUES_UPDATE = 301
    ISSUES_STATUS_CHANGE = 302
    ISSUES_COMMENT_ON_ISSUE = 303

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
    104) close pull request
2 todo
    200) create
    201) doing
    202) done
    203) change process
    204) comment on todo
    205) assign to xxx
3 issues
    300) create
    301) update
    302) status change
    303) comment on issue
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
