# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from gitshell.repos.models import Repos

LANG_CHOICES = (('C', 'C'), ('Java', 'Java'), ('C++', 'C++'), ('Objective-C', 'Objective-C'), ('PHP', 'PHP'), ('Python', 'Python'), ('JavaScript', 'JavaScript'), ('Ruby', 'Ruby'), ('C#', 'C#'), ('Erlang', 'Erlang'), ('Bash', 'Bash'), ('Awk', 'Awk'), ('Scala', 'Scala'), ('Haskell', 'Haskell'), ('Perl', 'Perl'), ('Lisp', 'Lisp'), ('PL/SQL', 'PL/SQL'), ('Lua', 'Lua'), ('(Visual)', '(Visual)'), ('Basic', 'Basic'), ('MATLAB', 'MATLAB'), ('Delphi/Object', 'Delphi/Object'), ('Pascal', 'Pascal'), ('Visual', 'Visual'), ('Basic', 'Basic'), ('.NET', '.NET'), ('Pascal', 'Pascal'), ('Ada', 'Ada'), ('Transact-SQL', 'Transact-SQL'), ('Logo', 'Logo'), ('NXT-G', 'NXT-G'), ('SAS', 'SAS'), ('Assembly', 'Assembly'), ('ActionScript', 'ActionScript'), ('Fortran', 'Fortran'), ('RPG', 'RPG'), ('(OS/400)', '(OS/400)'), ('Scheme', 'Scheme'), ('COBOL', 'COBOL'), ('Groovy', 'Groovy'), ('R', 'R'), ('ABAP', 'ABAP'), ('cg', 'cg'), ('Scratch', 'Scratch'), ('D', 'D'), ('Prolog', 'Prolog'), ('F#', 'F#'), ('APL', 'APL'), ('Smalltalk', 'Smalltalk'), ('(Visual)', '(Visual)'), ('FoxPro', 'FoxPro'), ('Forth', 'Forth'), ('ML', 'ML'), ('Alice', 'Alice'), ('CFML', 'CFML'), ('VBScript', 'VBScript'), ('other', '其他'))
AUTH_TYPE_CHOICES = (('0', '公开'), ('1', '半公开'), ('2', '私有'))

class ReposForm(forms.ModelForm):
    class Meta:
        model = Repos
        fields = ('name', 'desc', 'lang', 'auth_type')
        required = {
            'desc': False,
        }
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': '64'}),
            'desc': forms.Textarea(attrs={'cols': 50, 'rows': 5, 'maxlength': 512}),
            'lang': forms.Select(attrs={'maxlength': 16}, choices=LANG_CHOICES),
            'auth_type': forms.RadioSelect(attrs={'maxlength': 10}, choices=AUTH_TYPE_CHOICES),
        }
