# -*- coding: utf-8 -*-

import time
from gitshell.repo.models import Issues

class RepoIssuesAttrs():

    def __init__(self, name, value):
        self.name = name
        self.value = value

TRACKERS = [RepoIssuesAttrs('缺陷', 0), RepoIssuesAttrs('功能', 1), RepoIssuesAttrs('支持', 2)]
STATUSES = [RepoIssuesAttrs('新建', 0), RepoIssuesAttrs('已指派', 1), RepoIssuesAttrs('进行中', 2), RepoIssuesAttrs('已解决', 3), RepoIssuesAttrs('已关闭', 4), RepoIssuesAttrs('已拒绝', 5)]
PRIORITIES = [RepoIssuesAttrs('紧急', 0), RepoIssuesAttrs('高', 1), RepoIssuesAttrs('普通', 2), RepoIssuesAttrs('低', 3)]
ISSUES_ATTRS = { 'TRACKERS': TRACKERS, 'STATUSES': STATUSES, 'PRIORITIES': PRIORITIES }

REV_TRACKERS = {0: '缺陷', 1: '功能', 2: '支持'}
REV_STATUSES = {0: '新建', 1: '已指派', 2: '进行中', 3: '已解决', 4: '已关闭', 5: '已拒绝'}
REV_PRIORITIES = {0: '紧急', 1: '高', 2: '普通', 3: '低'}

def conver_issues(raw_issues, user_map):
    issues = []
    for raw_issue in raw_issues:
        issue = {}
        issue['id'] = raw_issue.id
        issue['subject'] = raw_issue.subject
        issue['user_id'] = user_map[raw_issue.user_id]
        issue['tracker'] = REV_TRACKERS[raw_issue.tracker]
        issue['status'] = REV_STATUSES[raw_issue.status]
        issue['assigned'] = user_map[raw_issue.assigned]
        issue['priority'] = REV_PRIORITIES[raw_issue.priority]
        issue['category'] = raw_issue.category
        issue['create_time'] = time.mktime(raw_issue.create_time.timetuple())
        issue['modify_time'] = time.mktime(raw_issue.modify_time.timetuple())
        issues.append(issue)
    return issues
