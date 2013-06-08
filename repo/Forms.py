# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from gitshell.repo.models import Repo, Issues, IssuesComment, RepoManager
from gitshell.gsuser.models import GsuserManager

LANG_CHOICES = (('C', 'C'), ('Java', 'Java'), ('C++', 'C++'), ('Objective-C', 'Objective-C'), ('PHP', 'PHP'), ('Python', 'Python'), ('JavaScript', 'JavaScript'), ('Ruby', 'Ruby'), ('C#', 'C#'), ('Erlang', 'Erlang'), ('Bash', 'Bash'), ('Awk', 'Awk'), ('Scala', 'Scala'), ('Haskell', 'Haskell'), ('Perl', 'Perl'), ('Lisp', 'Lisp'), ('PL/SQL', 'PL/SQL'), ('Lua', 'Lua'), ('(Visual)', '(Visual)'), ('Basic', 'Basic'), ('MATLAB', 'MATLAB'), ('Delphi/Object', 'Delphi/Object'), ('Pascal', 'Pascal'), ('Visual', 'Visual'), ('Basic', 'Basic'), ('.NET', '.NET'), ('Pascal', 'Pascal'), ('Ada', 'Ada'), ('Transact-SQL', 'Transact-SQL'), ('Logo', 'Logo'), ('NXT-G', 'NXT-G'), ('SAS', 'SAS'), ('Assembly', 'Assembly'), ('ActionScript', 'ActionScript'), ('Fortran', 'Fortran'), ('RPG', 'RPG'), ('(OS/400)', '(OS/400)'), ('Scheme', 'Scheme'), ('COBOL', 'COBOL'), ('Groovy', 'Groovy'), ('R', 'R'), ('ABAP', 'ABAP'), ('cg', 'cg'), ('Scratch', 'Scratch'), ('D', 'D'), ('Prolog', 'Prolog'), ('F#', 'F#'), ('APL', 'APL'), ('Smalltalk', 'Smalltalk'), ('(Visual)', '(Visual)'), ('FoxPro', 'FoxPro'), ('Forth', 'Forth'), ('ML', 'ML'), ('Alice', 'Alice'), ('CFML', 'CFML'), ('VBScript', 'VBScript'), ('other', '其他'))
AUTH_TYPE_CHOICES = (('0', '公开'), ('1', '半公开'), ('2', '私有'))
#AUTH_TYPE_CHOICES = (('0', '公开'), ('2', '私有'))

class RepoForm(forms.ModelForm):
    class Meta:
        model = Repo
        fields = ('name', 'desc', 'lang', 'auth_type',)
        widgets = {
            'desc': forms.Textarea(attrs={'cols': 50, 'rows': 5, 'maxlength': 512}),
            'lang': forms.Select(choices=LANG_CHOICES),
            'auth_type': forms.RadioSelect(choices=AUTH_TYPE_CHOICES),
        }

TRACKER_CHOICES = (('1', '缺陷'), ('2', '功能'), ('3', '支持'))
STATUS_CHOICES = (('1', '新建'), ('2', '已指派'), ('3', '进行中'), ('4', '已解决'), ('5', '已关闭'), ('6', '已拒绝'))
PRIORITY_CHOICES = (('1', '紧急'), ('2', '高'), ('3', '普通'), ('4', '低'))
ASSIGNED_CHOICES = ()

class RepoIssuesForm(forms.ModelForm):

    def fill_assigned(self, repo):
        if repo is None:
            return
        members = RepoManager.list_repomember(repo.id)
        user_ids = [ m.user_id for m in members ]
        user_ids.insert(0, repo.user_id)
        user_list = GsuserManager.list_user_by_ids(user_ids)
        self.fields['assigned'] = forms.ChoiceField(choices=[ (o.id, o.username) for o in user_list ])

    class Meta:
        model = Issues
        fields = ('subject', 'tracker', 'status', 'assigned', 'priority', 'category', 'content',)
        widgets = {
            'content': forms.Textarea(attrs={'maxlength': 1024}),
            'assigned': forms.Select(choices=ASSIGNED_CHOICES),
            'tracker': forms.Select(choices=TRACKER_CHOICES),
            'status': forms.Select(choices=STATUS_CHOICES),
            'priority': forms.Select(choices=PRIORITY_CHOICES),
        }

class RepoIssuesCommentForm(forms.ModelForm):
    class Meta:
        model = IssuesComment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'maxlength': 1024}),
        }

class RepoMemberForm(forms.Form):
    username = forms.CharField(max_length=30)
    action = forms.CharField(max_length=30)
