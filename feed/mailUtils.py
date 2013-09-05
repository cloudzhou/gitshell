# -*- coding:utf-8 -*- 
import base64
import random, re, json, time
from smtplib import SMTP
from email import Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from django.core.cache import cache
from django.core.mail import send_mail
from gitshell.settings import logger

class Mailer():

    default_sender = u'Gitshell<noreply@gitshell.com>'

    def __init__(self):
        pass

    def send_mail(self, header, body, sender, receivers):
        try:
            send_mail(header, body, sender, receivers, fail_silently=False)
        except Exception, e:
            logger.exception(e)

    def send_html_mail(self, header, body, sender, receivers):
        if not sender:
            sender = self.default_sender
        smtp = SMTP('localhost', 25)
        for receiver in receivers:
            try:
                msg = MIMEMultipar('alternative')
                msg['Subject'] = header
                msg['From'] = sender
                msg['To'] = receiver
                mIMEText = MIMEText(body, 'html', 'utf-8')
                msg.attach(mIMEText)
                smtp.sendmail(sender, receiver, msg.as_string())
            except Exception, e:
                logger.exception(e)
        smtp.quit()

    def send_verify_email(self, user, eid, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash + '_useremail_id', eid)
        active_url = 'https://gitshell.com/settings/email/verified/%s/' % random_hash
        header = u'[Gitshell]验证邮件地址'
        body = u'尊敬的 %s：\n请点击下面的地址验证您在Gitshell的邮箱：\n%s\n----------\n此邮件由Gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % (user.username, active_url)
        self.send_mail(header, body, self.default_sender, [email])

    def send_change_email(self, user, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash, email)
        active_url = 'https://gitshell.com/settings/validate_email/%s/' % random_hash
        header = u'[Gitshell]更改邮件地址'
        body = u'尊敬的 %s：\n请点击下面的地址更改您在Gitshell的登录邮箱：\n%s\n----------\n此邮件由Gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % (user.username, active_url)
        self.send_mail(header, body, self.default_sender, [email])

    def send_verify_account(self, email, username, password):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash + '_email', email)
        cache.set(random_hash + '_username', username)
        cache.set(random_hash + '_password', password)
        active_url = 'https://gitshell.com/join/%s/' % random_hash
        header = u'[Gitshell]注册邮件'
        body = u'尊敬的Gitshell用户：\n感谢您选择了Gitshell，请点击下面的地址激活您在Gitshell的帐号：\n%s\n----------\n此邮件由Gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
        self.send_mail(header, body, self.default_sender, [email])

    def send_resetpassword(self, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash, email)
        active_url = 'https://gitshell.com/resetpassword/%s/' % random_hash
        header = u'[Gitshell]重置密码邮件'
        body = u'尊敬的Gitshell用户：\n如果您没有重置密码的请求，请忽略此邮件。点击下面的地址重置您在Gitshell的帐号密码：\n%s\n----------\n此邮件由Gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
        self.send_mail(header, body, self.default_sender, [email])


NOTIF_MAIL_TEMPLATE = """<html><head><title>{{title}}</title></head><body>
<div id=":vt" style="overflow: hidden;"><div><div style="min-width:600px;margin:0 auto;padding:39px;font-family:'Helvetica Neue',Helvetica,Arial,Sans-serif;font-size:13px;line-height:1.7;background-color:#f5f5f5" marginheight="0" marginwidth="0">
<table border="0" cellspacing="0" cellpadding="0" width="552" style="border:1px solid #dedede;border-bottom:2px solid #dedede;margin:0 auto;background-color:#ffffff"><tbody>
          {% for notifMessage in notifMessages %}
          <tr>
            <td><a href="/{{notifMessage.relative_name}}/">@{{notifMessage.relative_name}}</a></td>
            <td>
                {% if notifMessage.notif_type == 0 %}
                <span class="muted">commit: </span>{{notifMessage.relative_obj.subject}}
                <span class="muted"><a href="/{{notifMessage.relative_obj.get_repo_username}}/">{{notifMessage.relative_obj.get_repo_username}}</a>/<a href="/{{notifMessage.relative_obj.get_repo_username}}/{{notifMessage.relative_obj.repo_name}}/">{{notifMessage.relative_obj.repo_name}}</a>:<a href="/{{notifMessage.relative_obj.get_repo_username}}/{{notifMessage.relative_obj.repo_name}}/commits/{{notifMessage.relative_obj.get_short_refname}}/">{{notifMessage.relative_obj.get_short_refname}}</a></span>
                {% elif notifMessage.notif_type == 1 %}
                <span class="muted">issue: </span>{{notifMessage.relative_obj.subject}} <a href="/{{notifMessage.relative_obj.username}}/">{{notifMessage.relative_obj.username}}</a>/<a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/">{{notifMessage.relative_obj.reponame}}</a> <a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/issues/{{notifMessage.relative_obj.id}}/">#{{notifMessage.relative_obj.id}}</a>
                {% elif notifMessage.notif_type == 2 %}
                <span class="muted">comment on issue: </span>{{notifMessage.relative_obj.content}} <a href="/{{notifMessage.relative_obj.username}}/">{{notifMessage.relative_obj.username}}</a>/<a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/">{{notifMessage.relative_obj.reponame}}</a> <a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/issues/{{notifMessage.relative_obj.issues_id}}/">#{{notifMessage.relative_obj.issues_id}}</a>
                {% elif notifMessage.notif_type == 10 %}
                <span class="muted">pull request 提到你: </span> <a href="/{{notifMessage.relative_obj.desc_repo.username}}/{{notifMessage.relative_obj.desc_repo.name}}/pull/{{notifMessage.relative_obj.id}}/">#{{notifMessage.relative_obj.id}} {{notifMessage.relative_obj.short_title}}</a>
                {% elif notifMessage.notif_type >= 100 and notifMessage.notif_type <= 105 %}
                <span class="muted">{{notifMessage.message}} pull request: <a href="/{{notifMessage.relative_obj.desc_repo.username}}/{{notifMessage.relative_obj.desc_repo.name}}/pull/{{notifMessage.relative_obj.id}}/">#{{notifMessage.relative_obj.id}} {{notifMessage.relative_obj.short_title}}</a>
                {% elif notifMessage.notif_type == 300 %}
                <span class="muted">{{notifMessage.message}} issue: {{notifMessage.relative_obj.subject}} <a href="/{{notifMessage.relative_obj.username}}/">{{notifMessage.relative_obj.username}}</a>/<a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/">{{notifMessage.relative_obj.reponame}}</a> <a href="/{{notifMessage.relative_obj.username}}/{{notifMessage.relative_obj.reponame}}/issues/{{notifMessage.relative_obj.id}}/">#{{notifMessage.relative_obj.id}}</a>
                {% endif %}
                <span class="unixtime">{{notifMessage.relative_obj.modify_time|date:"U"}}</span>
            </td>
          </tr>
          {% endfor %}
</tbody></table>
</div></div></div></body></html>
"""

