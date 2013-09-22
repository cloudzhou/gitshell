# -*- coding: utf-8 -*-  
import os, time, re
from django.db import models
from django.core.cache import cache
from gitshell.objectscache.models import BaseModel, CacheKey
from gitshell.objectscache.da import query, query_first, queryraw, execute, count, get, get_many, get_version, get_sqlkey, get_raw, get_raw_many

class Issue(BaseModel):
    user_id = models.IntegerField()
    repo_id = models.IntegerField()
    creator_user_id = models.IntegerField()
    subject = models.CharField(max_length=128, default='')
    tracker = models.IntegerField(default=0)
    status = models.IntegerField(default=0) 
    assigned = models.IntegerField(default=0)
    priority = models.IntegerField(default=0)
    category = models.CharField(max_length=16, default='')
    content = models.CharField(max_length=1024, default='')
    comment_count = models.IntegerField(default=0)

    # field without database
    username = ''
    reponame = ''

class IssueComment(BaseModel):
    issue_id = models.IntegerField()
    user_id = models.IntegerField()
    vote = models.IntegerField(default=0)
    content = models.CharField(max_length=512, default='') 

    # field without database
    username = ''
    reponame = ''

class ISSUE_STATUS:

    NEW = 1
    ASSIGNED = 2
    INPROGRESS = 3
    RESOLVED = 4
    CLOSED = 5
    REJECTED = 6

    VIEW_MAP = {
        1 : '新建',
        2 : '已指派',
        3 : '进行中',
        4 : '已解决',
        5 : '已关闭',
        6 : '已拒绝',
    }

class IssueManager():

    @classmethod
    def list_issues_cons(self, repo_id, assigned_ids, trackers, statuses, priorities, orderby, offset, row_count):
        # diff between multi filter and single filter
        rawsql_id = 'issue.list_issues_cons'
        parameters = [
            ','.join(str(x) for x in assigned_ids),
            ','.join(str(x) for x in trackers),
            ','.join(str(x) for x in statuses),
            ','.join(str(x) for x in priorities),
            orderby, offset, row_count]
        version = get_version(Issue, repo_id)
        sqlkey = get_sqlkey(version, rawsql_id, parameters)
        value = cache.get(sqlkey)
        if value is not None:
            return get_many(Issue, value)
        issues = Issue.objects.filter(visibly=0).filter(repo_id=repo_id).filter(assigned__in=assigned_ids).filter(tracker__in=trackers).filter(status__in=statuses).filter(priority__in=priorities).order_by('-'+orderby)[offset : offset+row_count]
        issues_ids = [x.id for x in issues]
        cache.add(sqlkey, issues_ids)
        return list(issues)

    @classmethod
    def list_issues(self, repo_id, orderby, offset, row_count):
        rawsql_id = 'issue_l_cons_modify'
        if orderby == 'create_time':
            rawsql_id = 'issue_l_cons_create'
        issues = query(Issue, repo_id, rawsql_id, [repo_id, offset, row_count]) 
        return issues

    @classmethod
    def list_issues_by_teamUserId_assigned(self, team_user_id, assigned, orderby, offset, row_count):
        rawsql_id = 'issue_l_userId_assigned_modify'
        if orderby == 'create_time':
            rawsql_id = 'issue_l_userId_assigned_create'
        assigned_issues = query(Issue, None, rawsql_id, [team_user_id, assigned, offset, row_count]) 
        return assigned_issues

    @classmethod
    def list_assigned_issues(self, assigned, orderby, offset, row_count):
        rawsql_id = 'issue_l_assigned_modify'
        if orderby == 'create_time':
            rawsql_id = 'issue_l_assigned_create'
        assigned_issues = query(Issue, None, rawsql_id, [assigned, offset, row_count]) 
        return assigned_issues

    @classmethod
    def get_issue_by_id(self, issue_id):
        return get(Issue, issue_id)

    @classmethod
    def get_issue(self, repo_id, issue_id):
        issue = query_first(Issue, repo_id, 'issue_s_id', [repo_id, issue_id])
        return issue

    @classmethod
    def get_issue_comment(self, comment_id):
        issue_comment = get(IssueComment, comment_id)
        return issue_comment

    @classmethod
    def list_issue_comments(self, issue_id, offset, row_count):
        issueComments = query(IssueComment, issue_id, 'issuecomment_l_issueId', [issue_id, offset, row_count]) 
        return issueComments



