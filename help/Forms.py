from django import forms
from captcha.fields import CaptchaField

class ResetAccessLimitForm(forms.Form):
    captcha = CaptchaField()
