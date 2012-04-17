# -*- coding: utf-8 -*-  
from django import forms
from captcha.fields import CaptchaField
from gitshell.gsuser.models import Userprofile

class UserprofileForm(forms.ModelForm):
    class Meta:
        model = Userprofile
        fields = ('nickname', 'company', 'website', 'location', 'tweet', 'resume')
        widgets = {
            'resume': forms.Textarea(attrs={'cols': 50, 'rows': 5}),
        }

class DoSshpubkeyForm(forms.Form):
    pubkey_id = forms.IntegerField()
    action = forms.CharField(max_length=12)

class SshpubkeyForm(forms.Form):
    pubkey_name = forms.CharField(max_length=12)
    pubkey = forms.CharField(max_length=1024, widget=forms.Textarea(attrs={'cols': 50, 'rows': 5}))

class ChangepasswordForm(forms.Form):
    old_password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
