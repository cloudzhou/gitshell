from django import forms
from captcha.fields import CaptchaField

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField()
    rememberme = forms.BooleanField(required=False)

class JoinForm0(forms.Form):
    email = forms.EmailField()
    captcha = CaptchaField()

class JoinForm1(forms.Form):
    user_name = forms.CharField(max_length=12)
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))

class ResetpasswordForm0(forms.Form):
    email = forms.EmailField()
    captcha = CaptchaField()

class ResetpasswordForm1(forms.Form):
    password = forms.CharField(max_length=64, widget=forms.PasswordInput(render_value=False))
