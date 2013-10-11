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

    category = forms.CharField(required=False)
    content = forms.CharField(widget=forms.Textarea, required=False)

    def fill_assigned(self, repo):
        if repo is None:
            return
        memberUsers = RepoManager.list_repo_team_memberUser(repo.id)
        self.fields['assigned'] = forms.ChoiceField(choices=[ (o.id, o.username) for o in memberUsers ])

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




