from django import forms
from captcha.fields import CaptchaField

class DosshpubkeyForm(forms.Form):
    user_pubkey_id = forms.IntegerField()
    action = forms.CharField(max_length=12)

class SshpubkeyForm(forms.Form):
    pubkey_name = forms.CharField(max_length=12)
    pubkey = forms.CharField(max_length=1024, widget=forms.Textarea(attrs={'cols': 50, 'rows': 5}))

class ChangepasswordForm(forms.Form):
    old_password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField()
