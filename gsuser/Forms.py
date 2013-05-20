from django import forms
from captcha.fields import CaptchaField

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=64)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
    #captcha = CaptchaField()
    rememberme = forms.BooleanField(required=False)

class JoinForm(forms.Form):
    email = forms.EmailField()
    username = forms.CharField(max_length=12)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
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

