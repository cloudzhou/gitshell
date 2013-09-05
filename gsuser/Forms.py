from django import forms
from captcha.fields import CaptchaField

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=64, widget=forms.TextInput(attrs={'id': 'email'}))
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False, attrs={'id': 'password'}))
    #captcha = CaptchaField()
    rememberme = forms.BooleanField(required=False)

class JoinForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'id': 'email'}))
    username = forms.CharField(max_length=24, widget=forms.TextInput(attrs={'id': 'username'}))
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False, attrs={'id': 'password'}))
    #captcha = CaptchaField()

class ResetpasswordForm0(forms.Form):
    email = forms.EmailField()

class ResetpasswordForm1(forms.Form):
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))

# skills and recommends
class SkillsForm(forms.Form):
    sid = forms.IntegerField()
    skills = forms.CharField(max_length=10)
    uid = forms.IntegerField()
    action = forms.CharField(max_length=3)

class RecommendsForm(forms.Form):
    content = forms.CharField(max_length=64)

