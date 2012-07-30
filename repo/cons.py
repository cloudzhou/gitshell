# -*- coding: utf-8 -*-

import time
from gitshell.repo.models import Repo, Issues
from gitshell.gsuser.models import GsuserManager
from django.forms.models import model_to_dict

class RepoIssuesAttrs():

    def __init__(self, name, value):
        self.name = name
        self.value = value

TRACKERS = [RepoIssuesAttrs('所有', 0), RepoIssuesAttrs('缺陷', 1), RepoIssuesAttrs('功能', 2), RepoIssuesAttrs('支持', 3)]
STATUSES = [RepoIssuesAttrs('所有', 0), RepoIssuesAttrs('新建', 1), RepoIssuesAttrs('已指派', 2), RepoIssuesAttrs('进行中', 3), RepoIssuesAttrs('已解决', 4), RepoIssuesAttrs('已关闭', 5), RepoIssuesAttrs('已拒绝', 6)]
PRIORITIES = [RepoIssuesAttrs('所有', 0), RepoIssuesAttrs('紧急', 1), RepoIssuesAttrs('高', 2), RepoIssuesAttrs('普通', 3), RepoIssuesAttrs('低', 4)]
TRACKERS_VAL = [1, 2, 3]
STATUSES_VAL = [1, 2, 3, 4, 5, 6]
PRIORITIES_VAL = [1, 2, 3, 4]

ISSUES_ATTRS = { 'TRACKERS': TRACKERS, 'STATUSES': STATUSES, 'PRIORITIES': PRIORITIES }

REV_TRACKERS = {1: '缺陷', 2: '功能', 3: '支持'}
REV_STATUSES = {1: '新建', 2: '已指派', 3: '进行中', 4: '已解决', 5: '已关闭', 6: '已拒绝'}
REV_PRIORITIES = {1: '紧急', 2: '高', 3: '普通', 4: '低'}

def conver_issues(raw_issues, user_map):
    issues = []
    for raw_issue in raw_issues:
        issue = {}
        issue['id'] = raw_issue.id
        issue['subject'] = raw_issue.subject
        issue['content'] = raw_issue.content
        if raw_issue.user_id in user_map:
            issue['user_id'] = user_map[raw_issue.user_id]
        issue['tracker'] = REV_TRACKERS[raw_issue.tracker]
        issue['status'] = REV_STATUSES[raw_issue.status]
        if raw_issue.assigned in user_map:
            issue['assigned'] = user_map[raw_issue.assigned]
        issue['priority'] = REV_PRIORITIES[raw_issue.priority]
        issue['category'] = raw_issue.category
        issue['create_time'] = time.mktime(raw_issue.create_time.timetuple())
        issue['modify_time'] = time.mktime(raw_issue.modify_time.timetuple())
        issue['comment_count'] = raw_issue.comment_count
        issues.append(issue)
    return issues

def conver_issue_comments(raw_issue_comments, user_map, user_img_map):
    issue_comments = []
    for raw_issue_comment in raw_issue_comments:
        issue_comment = {}
        issue_comment['id'] = raw_issue_comment.id
        if raw_issue_comment.user_id in user_map:
            issue_comment['user_id'] = user_map[raw_issue_comment.user_id]
        if raw_issue_comment.user_id in user_img_map:
            issue_comment['user_img'] = user_img_map[raw_issue_comment.user_id]
        issue_comment['content'] = raw_issue_comment.content
        issue_comment['create_time'] = time.mktime(raw_issue_comment.create_time.timetuple())
        issue_comments.append(issue_comment)
    return issue_comments

def conver_repos(raw_repos, map_users):
    repos_vo = []
    for raw_repo in raw_repos:
        repo_dict = model_to_dict(raw_repo, fields=[field.name for field in Repo._meta.fields])
        repo_dict['id'] = raw_repo.id
        repo_dict['create_time'] = time.mktime(raw_repo.create_time.timetuple())
        repo_dict['modify_time'] = time.mktime(raw_repo.modify_time.timetuple())
        if raw_repo.user_id in map_users:
            repo_dict['username'] = map_users[raw_repo.user_id]['username']
            repo_dict['imgurl'] = map_users[raw_repo.user_id]['imgurl']
        repos_vo.append(repo_dict) 
    return repos_vo
