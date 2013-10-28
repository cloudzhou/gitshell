# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from gitshell.repo.models import Repo, RepoManager
from gitshell.feed.feed import AttrKey, FeedAction
from gitshell.gsuser.models import GsuserManager
from gitshell.team.models import TeamManager

LANG_CHOICES = (('C', 'C'), ('Java', 'Java'), ('C++', 'C++'), ('Objective-C', 'Objective-C'), ('PHP', 'PHP'), ('Python', 'Python'), ('JavaScript', 'JavaScript'), ('Ruby', 'Ruby'), ('C#', 'C#'), ('Erlang', 'Erlang'), ('Bash', 'Bash'), ('Awk', 'Awk'), ('Scala', 'Scala'), ('Go', 'Go'), ('Haskell', 'Haskell'), ('Perl', 'Perl'), ('Lisp', 'Lisp'), ('PL/SQL', 'PL/SQL'), ('Lua', 'Lua'), ('(Visual)', '(Visual)'), ('Basic', 'Basic'), ('MATLAB', 'MATLAB'), ('Delphi/Object', 'Delphi/Object'), ('Pascal', 'Pascal'), ('Visual', 'Visual'), ('Basic', 'Basic'), ('.NET', '.NET'), ('Pascal', 'Pascal'), ('Ada', 'Ada'), ('Transact-SQL', 'Transact-SQL'), ('Logo', 'Logo'), ('NXT-G', 'NXT-G'), ('SAS', 'SAS'), ('Assembly', 'Assembly'), ('ActionScript', 'ActionScript'), ('Fortran', 'Fortran'), ('RPG', 'RPG'), ('(OS/400)', '(OS/400)'), ('Scheme', 'Scheme'), ('COBOL', 'COBOL'), ('Groovy', 'Groovy'), ('R', 'R'), ('ABAP', 'ABAP'), ('cg', 'cg'), ('Scratch', 'Scratch'), ('D', 'D'), ('Prolog', 'Prolog'), ('F#', 'F#'), ('APL', 'APL'), ('Smalltalk', 'Smalltalk'), ('(Visual)', '(Visual)'), ('FoxPro', 'FoxPro'), ('Forth', 'Forth'), ('ML', 'ML'), ('Alice', 'Alice'), ('CFML', 'CFML'), ('VBScript', 'VBScript'), ('other', '其他'))
AUTH_TYPE_CHOICES = (('2', '私有'), ('0', '公开'), ('1', '半公开'))

class RepoForm(forms.ModelForm):

    def fill_username(self, userprofile, owner_user_id):
        feedAction = FeedAction()
        teamMembers = TeamManager.list_teamMember_by_userId(userprofile.id)
        username_choices = []
        username_choices.append((userprofile.username, userprofile.username))
        for teamMember in teamMembers:
            if teamMember.team_user_id == owner_user_id:
                username_choices.insert(0, (teamMember.team_user.username, teamMember.team_user.username))
                continue
            username_choices.append((teamMember.team_user.username, teamMember.team_user.username))
        self.fields['username'] = forms.ChoiceField(choices=username_choices, required=False)

    class Meta:
        model = Repo
        fields = ('username', 'name', 'desc', 'lang', 'auth_type',)
        widgets = {
            'desc': forms.Textarea(attrs={'cols': 60, 'rows': 5, 'maxlength': 512}),
            'lang': forms.Select(choices=LANG_CHOICES),
            'auth_type': forms.RadioSelect(choices=AUTH_TYPE_CHOICES),
        }

