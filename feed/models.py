# -*- coding: utf-8 -*-  
import re, time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db import models
from django.core.cache import cache
from django.template import Context, Template
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, query_first, queryraw, execute, count, get, get_many, get_version, get_sqlkey
from gitshell.objectscache.da import get_raw, get_raw_many
from gitshell.gsuser.models import GsuserManager
from gitshell.repo.models import RepoManager, PullRequest, PULL_STATUS
from gitshell.issue.models import IssueManager, ISSUE_STATUS
from gitshell.feed.feed import FeedAction
from gitshell.feed.mailUtils import Mailer, NOTIF_MAIL_TEMPLATE

class Feed(BaseModel):
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

class NotifMessage(BaseModel):
    user_id = models.IntegerField(default=0)
    repo_id = models.IntegerField(default=0)
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
    def create_at_merge(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_MERGE, from_user_id, to_user_id, relative_id)

    @classmethod
    def create_at_issue(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_ISSUE, from_user_id, to_user_id, relative_id)

    @classmethod
    def create_at_issue_comment(self, from_user_id, to_user_id, relative_id):
        return self.create(NOTIF_CATE.AT, NOTIF_TYPE.AT_ISSUE_COMMENT, from_user_id, to_user_id, relative_id)

    def is_at_commit(self):
        return self.notif_type == NOTIF_TYPE.AT_COMMIT
    def is_at_merge(self):
        return self.notif_type == NOTIF_TYPE.AT_MERGE
    def is_at_issue(self):
        return self.notif_type == NOTIF_TYPE.AT_ISSUE
    def is_at_issue_comment(self):
        return self.notif_type == NOTIF_TYPE.AT_ISSUE_COMMENT

    def is_issue_cate(self):
        return self.notif_cate == NOTIF_CATE.ISSUES
    def is_pull_request_cate(self):
        return self.notif_cate == NOTIF_CATE.MERGE

class NotifSetting(BaseModel):
    user_id = models.IntegerField(default=0)
    notif_types = models.CharField(max_length=1024, null=True)
    notif_fqcy = models.IntegerField(default=0)
    last_notif_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    expect_notif_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    email = models.CharField(max_length=75, null=True)

    def get_notif_types(self):
        types = []
        if self.notif_types == 'all':
            return NOTIF_TYPE.VALUES
        for x in self.notif_types.split(','):
            if not re.match('^\d+$', x):
                continue
            type_ = int(x)
            if type_ in NOTIF_TYPE.VALUES:
                types.append(type_);
        return types

class FeedManager():

    @classmethod
    def list_notifmessage_by_userId(self, user_id, offset, row_count):
        notifMessages = query(NotifMessage, user_id, 'notifmessage_l_toUserId', [user_id, offset, row_count])
        return self._fillwith_notifMessages(notifMessages)

    @classmethod
    def list_notifmessage_by_teamUserId_toUserId(self, team_user_id, to_user_id, offset, row_count):
        notifMessages = query(NotifMessage, None, 'notifmessage_l_userId_toUserId', [team_user_id, to_user_id, offset, row_count])
        return self._fillwith_notifMessages(notifMessages)

    @classmethod
    def list_notifmessage_by_userId_betweenTime_notifTypes(self, user_id, from_time, to_time, notif_types, offset, row_count):
        notifMessages = []
        if notif_types == 'all':
            notifMessages = query(NotifMessage, user_id, 'notifmessage_l_toUserId_modifyTime', [user_id, from_time, to_time, offset, row_count])
        else:
            filtered_notif_types = []
            split_notif_types = notif_types.split(',')
            for split_notif_type in split_notif_types:
                if re.match('^\d+$', split_notif_type):
                    filtered_notif_types.append(int(split_notif_type))
            if len(filtered_notif_types) == 0:
                return []
            notifMessages = list(NotifMessage.objects.filter(visibly=0).filter(to_user_id=user_id).filter(modify_time__gt=from_time).filter(modify_time__lte=to_time).filter(notif_type__in=filtered_notif_types).order_by('-modify_time')[offset : offset+row_count])
        return self._fillwith_notifMessages(notifMessages)

    @classmethod
    def _fillwith_notifMessages(self, notifMessages):
        for notifMessage in notifMessages:
            relative_user = GsuserManager.get_user_by_id(notifMessage.from_user_id)
            if relative_user is not None:
                notifMessage.relative_name = relative_user.username
            if notifMessage.is_at_commit():
                commitHistory = RepoManager.get_commit_by_id(notifMessage.relative_id)
                notifMessage.relative_obj = commitHistory
            elif notifMessage.is_at_issue() or notifMessage.is_issue_cate():
                issue = IssueManager.get_issue_by_id(notifMessage.relative_id)
                if issue is not None:
                    repo = RepoManager.get_repo_by_id(issue.repo_id)
                    if repo is not None:
                        issue.username = repo.username
                        issue.reponame = repo.name
                notifMessage.relative_obj = issue
            elif notifMessage.is_at_issue_comment():
                issue_comment = IssueManager.get_issue_comment(notifMessage.relative_id)
                if not issue_comment: 
                    continue
                issue = IssueManager.get_issue_by_id(issue_comment.issue_id)
                if issue is not None:
                    repo = RepoManager.get_repo_by_id(issue.repo_id)
                    if repo is not None:
                        issue_comment.username = repo.username
                        issue_comment.reponame = repo.name
                notifMessage.relative_obj = issue_comment
            elif notifMessage.is_at_merge() or notifMessage.is_pull_request_cate():
                pullRequest = RepoManager.get_pullRequest_by_id(notifMessage.relative_id)
                notifMessage.relative_obj = pullRequest
        return notifMessages

    @classmethod
    def get_notifmessage_by_userId_notifType_relativeId(self, user_id, notif_type, relative_id):
        notifMessage = query_first(NotifMessage, user_id, 'notifmessage_s_toUserId_notifType_relativeId', [user_id, notif_type, relative_id])
        return notifMessage

    @classmethod
    def list_notifsetting_by_expectNotifTime(self, expect_notif_time, offset, row_count):
        notifSettings = query(NotifSetting, None, 'notifsetting_l_expectNotifTime', [expect_notif_time, offset, row_count])
        return notifSettings
        
    @classmethod
    def get_notifsetting_by_userId(self, user_id):
        notifSetting = query_first(NotifSetting, user_id, 'notifsetting_s_userId', [user_id])
        if not notifSetting:
            userprofile = GsuserManager.get_userprofile_by_id(user_id)
            if not userprofile:
                return None
            notifSetting = NotifSetting(
                user_id = user_id,
                notif_types = 'all',
                notif_fqcy = 0,
                email = userprofile.email,
            )
            notifSetting.save()
        return notifSetting

    @classmethod
    def list_feed_by_ids(self, ids):
        feeds = get_many(Feed, ids)
        return feeds

    @classmethod
    def feed_issue_change(self, user, repo, orgi_issue, current_issue_id):
        current_issue = IssueManager.get_issue_by_id(current_issue_id)
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
                status_changes.append(u'跟踪: ' + ISSUE_ATTR_DICT.TRACKER[current_issue.tracker])
            if orgi_issue.status != current_issue.status:
                status_changes.append(u'状态: ' + ISSUE_ATTR_DICT.STATUS[current_issue.status])
            if orgi_issue.assigned != current_issue.assigned:
                assigned_user = GsuserManager.get_user_by_id(current_issue.assigned)
                if assigned_user is not None:
                    status_changes.append(u'指派给: @' + assigned_user.username)
            if orgi_issue.priority != current_issue.priority:
                status_changes.append(u'优先级: ' + ISSUE_ATTR_DICT.PRIORITY[current_issue.priority])
            
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
    def notif_at(self, notif_type, from_user_id, relative_id, message):
        at_name_list = FeedUtils.list_atname(message)
        user_unread_message_dict = {}

        for at_name in at_name_list:
            at_user = GsuserManager.get_user_by_name(at_name)
            if at_user is not None:
                to_user_id = at_user.id
                notifMessage = None
                # disable duplicate notify
                exists_notifMessage = self.get_notifmessage_by_userId_notifType_relativeId(to_user_id, notif_type, relative_id)
                if exists_notifMessage is not None:
                    continue
                if notif_type == NOTIF_TYPE.AT_COMMIT:
                    notifMessage = NotifMessage.create_at_commit(from_user_id, to_user_id, relative_id)
                elif notif_type == NOTIF_TYPE.AT_MERGE:
                    notifMessage = NotifMessage.create_at_merge(from_user_id, to_user_id, relative_id)
                elif notif_type == NOTIF_TYPE.AT_ISSUE:
                    notifMessage = NotifMessage.create_at_issue(from_user_id, to_user_id, relative_id)
                elif notif_type == NOTIF_TYPE.AT_ISSUE_COMMENT:
                    notifMessage = NotifMessage.create_at_issue_comment(from_user_id, to_user_id, relative_id)
                if notifMessage is None:
                    continue
                self.message_save_and_notif(notifMessage)
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
    def notif_issue_status(self, user, issue, issueStatus):
        notif_cat = NOTIF_CATE.ISSUES
        message = ''
        if issueStatus == ISSUE_STATUS.ASSIGNED:
            notif_type = NOTIF_TYPE.ISSUE_ASSIGNED
            message = 'assigned'
            exists_notifMessage = self.get_notifmessage_by_userId_notifType_relativeId(issue.assigned, notif_type, issue.id)
            if exists_notifMessage:
                return
            assigned_userprofile = GsuserManager.get_userprofile_by_id(issue.assigned)
            if assigned_userprofile:
                notifMessage = NotifMessage.create(notif_cat, notif_type, user.id, issue.assigned, issue.id)
                notifMessage.message = message
                self.message_save_and_notif(notifMessage)
            assigned_userprofile.unread_message = assigned_userprofile.unread_message + 1
            assigned_userprofile.save()
        else:
            return

    @classmethod
    def notif_pull_request_status(self, pullRequest, pullStatus):
        notif_type = NOTIF_TYPE.MERGE_CREATE_PULL_REQUEST
        message = ''
        if pullStatus == PULL_STATUS.NEW:
            message = 'created'
            merge_user_profile = GsuserManager.get_userprofile_by_id(pullRequest.merge_user_id)
            if merge_user_profile is not None:
                notifMessage = NotifMessage.create(NOTIF_CATE.MERGE, NOTIF_TYPE.MERGE_CREATE_PULL_REQUEST, pullRequest.pull_user_id, pullRequest.merge_user_id, pullRequest.id)
                notifMessage.message = message
                self.message_save_and_notif(notifMessage)
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
            self.message_save_and_notif(notifMessage)
        pull_user_profile.unread_message = pull_user_profile.unread_message + 1
        pull_user_profile.save()

    @classmethod
    def render_notifMessages_as_html(self, userprofile, header, notifMessages):
        t = Template(NOTIF_MAIL_TEMPLATE)
        c = Context({'userprofile': userprofile, 'title': header, 'notifMessages': notifMessages})
        return t.render(c)

    @classmethod
    def message_save_and_notif(self, notifMessage):
        notifMessage.save()
        userprofile = GsuserManager.get_userprofile_by_id(notifMessage.to_user_id)
        header = u'来自Gitshell的通知'
        notifSetting = self.get_notifsetting_by_userId(notifMessage.to_user_id)
        last_notif_time = notifSetting.last_notif_time
        if not last_notif_time:
            last_notif_time = datetime.now()
        notif_fqcy = notifSetting.notif_fqcy
        if notif_fqcy == 0:
            notifMessage = self._fillwith_notifMessages([notifMessage])[0]
            html = self.render_notifMessages_as_html(userprofile, header, [notifMessage])
            Mailer().send_html_mail(header, html, None, [notifSetting.email])
        if notif_fqcy > 0:
            expect_notif_time = last_notif_time + timedelta(minutes=notif_fqcy)
            if expect_notif_time != notifSetting.expect_notif_time:
                notifSetting.expect_notif_time = expect_notif_time
                notifSetting.save()

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
        1: u'缺陷',
        2: u'功能',
        3: u'支持',
    }
    STATUS = {
        1: u'新建',
        2: u'已指派',
        3: u'进行中',
        4: u'已解决',
        5: u'已关闭',
        6: u'已拒绝',
    }
    PRIORITY = {
        1: u'紧急',
        2: u'高',
        3: u'普通',
        4: u'低',
    }

class NOTIF_FQCY:

    NEVER = -1
    NOW = 0
    PER_5MIN = 5
    PER_15MIN = 15
    PER_30MIN = 30
    PER_45MIN = 45
    PER_1HOUR = 60
    PER_3HOUR = 180
    PER_6HOUR = 360
    PER_12HOUR = 720
    PER_1DAY = 1440

    NOTIF_FQCY_CHOICE = [
        {'key': u'永远不', 'value': -1},
        {'key': u'尽可能快', 'value': 0},
        {'key': u'5分钟', 'value': 5},
        {'key': u'15分钟', 'value': 15},
        {'key': u'30分钟', 'value': 30},
        {'key': u'45分钟', 'value': 45},
        {'key': u'1小时', 'value': 60},
        {'key': u'3小时', 'value': 180},
        {'key': u'6小时', 'value': 360},
        {'key': u'12小时', 'value': 720},
        {'key': u'24小时', 'value': 1440},
    ]

    VALUES = [-1, 0, 5, 15, 30, 45, 60, 180, 360, 720, 1440]

class NOTIF_CATE:

    AT = 0
    MERGE = 1
    TODO = 2
    ISSUES = 3
    ACTIVE = 4

class NOTIF_TYPE:

    AT_COMMIT = 0
    AT_MERGE = 10
    AT_MERGE_COMMENT = 11
    AT_ISSUE = 30
    AT_ISSUE_COMMENT = 31

    MERGE_CREATE_PULL_REQUEST = 100
    MERGE_MERGED_PULL_REQUEST = 101
    MERGE_MERGED_FAILED_PULL_REQUEST = 102
    MERGE_REJECTED_PULL_REQUEST = 103
    MERGE_CLOSE_PULL_REQUEST = 104
    MERGE_COMMENT_ON_PULL_REQUEST = 105
    
    ISSUE_ASSIGNED = 300
    ISSUE_UPDATE = 301
    ISSUE_STATUS_CHANGE = 302
    ISSUE_COMMENT_ON_ISSUE = 303

    NOTIF_TYPE_CHOICE = {
        'at': [
            {'key': u'Commit 提交信息', 'value': 0},
            {'key': u'Pull Request 内容', 'value': 10},
            {'key': u'Pull Request 评论', 'value': 11},
            {'key': u'Issue 内容', 'value': 30},
            {'key': u'Issue 评论', 'value': 31},
        ],
        'merge': [
            {'key': u'需要你参与', 'value': 100},
            {'key': u'合并成功', 'value': 101},
            {'key': u'合并失败', 'value': 102},
            {'key': u'被拒绝', 'value': 103},
            {'key': u'被关闭', 'value': 104},
            {'key': u'评论', 'value': 105},
        ],
        'issue': [
            {'key': u'需要你参与', 'value': 300},
            {'key': u'有更新', 'value': 301},
            {'key': u'状态改变', 'value': 302},
            {'key': u'评论', 'value': 303},
        ],
    }

    VALUES = [0, 10, 11, 30, 31, 100, 101, 102, 103, 104, 105, 300, 301, 302, 303]

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
