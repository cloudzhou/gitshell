# -*- coding: utf-8 -*-
from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from captcha.fields import CaptchaField

LANG_CHOICES = (('C', 'C'), ('Java', 'Java'), ('C++', 'C++'), ('Objective-C', 'Objective-C'), ('PHP', 'PHP'), ('Python', 'Python'), ('JavaScript', 'JavaScript'), ('Ruby', 'Ruby'), ('C#', 'C#'), ('Erlang', 'Erlang'), ('Bash', 'Bash'), ('Awk', 'Awk'), ('Scala', 'Scala'), ('Haskell', 'Haskell'), ('Perl', 'Perl'), ('Lisp', 'Lisp'), ('PL/SQL', 'PL/SQL'), ('Lua', 'Lua'), ('(Visual)', '(Visual)'), ('Basic', 'Basic'), ('MATLAB', 'MATLAB'), ('Delphi/Object', 'Delphi/Object'), ('Pascal', 'Pascal'), ('Visual', 'Visual'), ('Basic', 'Basic'), ('.NET', '.NET'), ('Pascal', 'Pascal'), ('Ada', 'Ada'), ('Transact-SQL', 'Transact-SQL'), ('Logo', 'Logo'), ('NXT-G', 'NXT-G'), ('SAS', 'SAS'), ('Assembly', 'Assembly'), ('ActionScript', 'ActionScript'), ('Fortran', 'Fortran'), ('RPG', 'RPG'), ('(OS/400)', '(OS/400)'), ('Scheme', 'Scheme'), ('COBOL', 'COBOL'), ('Groovy', 'Groovy'), ('R', 'R'), ('ABAP', 'ABAP'), ('cg', 'cg'), ('Scratch', 'Scratch'), ('D', 'D'), ('Prolog', 'Prolog'), ('F#', 'F#'), ('APL', 'APL'), ('Smalltalk', 'Smalltalk'), ('(Visual)', '(Visual)'), ('FoxPro', 'FoxPro'), ('Forth', 'Forth'), ('ML', 'ML'), ('Alice', 'Alice'), ('CFML', 'CFML'), ('VBScript', 'VBScript'), ('other', '其他'))
AUTH_TYPE_CHOICES = (('pub', '公开'), ('hpu', '半公开'), ('pri', '私有'))

class EditForm(forms.Form):
    rid = forms.IntegerField()
    name = forms.CharField(max_length=64)
    desc = forms.CharField(max_length=256)
    lang = forms.ChoiceField(choices=LANG_CHOICES)
    other_lang =  forms.CharField(max_length=16)
    auth_type = forms.ChoiceField(widget=RadioSelect, choices=AUTH_TYPE_CHOICES)

class JoinForm0(forms.Form):
    email = forms.EmailField()
    captcha = CaptchaField()

class JoinForm1(forms.Form):
    name = forms.CharField(max_length=12)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))

class ResetpasswordForm0(forms.Form):
    email = forms.EmailField()
    captcha = CaptchaField()

class ResetpasswordForm1(forms.Form):
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))

