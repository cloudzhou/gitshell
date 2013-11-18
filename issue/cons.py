# -*- coding: utf-8 -*-

import time
from gitshell.issue.models import Issue
from gitshell.gsuser.models import GsuserManager
from gitshell.repo.models import RepoManager
from django.forms.models import model_to_dict

class IssueAttrs():

    def __init__(self, name, value):
        self.name = name
        self.value = value

TRACKERS = [IssueAttrs('所有', 0), IssueAttrs('缺陷', 1), IssueAttrs('功能', 2), IssueAttrs('支持', 3)]
STATUSES = [IssueAttrs('所有', 0), IssueAttrs('新建', 1), IssueAttrs('已指派', 2), IssueAttrs('进行中', 3), IssueAttrs('已解决', 4), IssueAttrs('已关闭', 5), IssueAttrs('已拒绝', 6)]
PRIORITIES = [IssueAttrs('所有', 0), IssueAttrs('紧急', 1), IssueAttrs('高', 2), IssueAttrs('普通', 3), IssueAttrs('低', 4)]
TRACKERS_VAL = [1, 2, 3]
STATUSES_VAL = [1, 2, 3, 4, 5, 6]
PRIORITIES_VAL = [1, 2, 3, 4]

ISSUE_ATTRS = { u'TRACKERS': TRACKERS, u'STATUSES': STATUSES, u'PRIORITIES': PRIORITIES }

REV_TRACKERS = {1: u'缺陷', 2: u'功能', 3: u'支持'}
REV_STATUSES = {1: u'新建', 2: u'已指派', 3: u'进行中', 4: u'已解决', 5: u'已关闭', 6: u'已拒绝'}
REV_PRIORITIES = {1: u'紧急', 2: u'高', 3: u'普通', 4: u'低'}

