# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from gitshell.issue.models import Issue, IssueComment
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager

TRACKER_CHOICES = (('1', '缺陷'), ('2', '功能'), ('3', '支持'))
STATUS_CHOICES = (('1', '新建'), ('2', '已指派'), ('3', '进行中'), ('4', '已解决'), ('5', '已关闭'), ('6', '已拒绝'))
PRIORITY_CHOICES = (('1', '紧急'), ('2', '高'), ('3', '普通'), ('4', '低'))
ASSIGNED_CHOICES = ()

class IssueForm(forms.ModelForm):

    def fill_assigned(self, repo):
        if repo is None:
            return
        members = RepoManager.list_repomember(repo.id)
        user_ids = [ m.user_id for m in members ]
        user_ids.insert(0, repo.user_id)
        user_list = GsuserManager.list_user_by_ids(user_ids)
        self.fields['assigned'] = forms.ChoiceField(choices=[ (o.id, o.username) for o in user_list ])

    class Meta:
        model = Issue
        fields = ('subject', 'tracker', 'status', 'assigned', 'priority', 'category', 'content',)
        widgets = {
            'content': forms.Textarea(attrs={'maxlength': 1024}),
            'assigned': forms.Select(choices=ASSIGNED_CHOICES),
            'tracker': forms.Select(choices=TRACKER_CHOICES),
            'status': forms.Select(choices=STATUS_CHOICES),
            'priority': forms.Select(choices=PRIORITY_CHOICES),
        }

class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'maxlength': 1024}),
        }




