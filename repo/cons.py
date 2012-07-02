#!/usr/bin/python
# -*- coding: utf-8 -*-

class RepoIssuesAttrs():

    def __init__(self, name, value):
        self.name = name
        self.value = value

TRACKERS = [RepoIssuesAttrs('缺陷', 0), RepoIssuesAttrs('功能', 1), RepoIssuesAttrs('支持', 2)]
STATUSES = [RepoIssuesAttrs('新建', 0), RepoIssuesAttrs('已指派', 1), RepoIssuesAttrs('进行中', 2), RepoIssuesAttrs('已解决', 3), RepoIssuesAttrs('已关闭', 4), RepoIssuesAttrs('已拒绝', 5)]
PRIORITIES = [RepoIssuesAttrs('紧急', 0), RepoIssuesAttrs('高', 1), RepoIssuesAttrs('普通', 2), RepoIssuesAttrs('低', 3)]
ISSUES_ATTRS = { 'TRACKERS': TRACKERS, 'STATUSES': STATUSES, 'PRIORITIES': PRIORITIES }
