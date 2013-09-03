# -*- coding:utf-8 -*- 
import random, re, json, time, smtplib
from django.core.cache import cache
from django.core.mail import send_mail
from email import Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from gitshell.settings import logger

class Mailer():

    sender = u'Gitshell<noreply@gitshell.com>'

    def __init__(self):
        pass

    def send_mail(self, header, body, sender, receivers):
        try:
            send_mail(header, body, sender, receivers, fail_silently=False)
        except Exception, e:
            logger.exception(e)

    def send_verify_email(self, user, eid, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash + '_useremail_id', eid)
        active_url = 'https://gitshell.com/settings/email/verified/%s/' % random_hash
        header = u'[gitshell]验证邮件地址'
        body = u'尊敬的 %s：\n请点击下面的地址验证您在gitshell的邮箱：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % (user.username, active_url)
        self.send_mail(header, body, self.sender, [email])

    def send_change_email(self, user, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash, email)
        active_url = 'https://gitshell.com/settings/validate_email/%s/' % random_hash
        header = u'[gitshell]更改邮件地址'
        body = u'尊敬的 %s：\n请点击下面的地址更改您在gitshell的登录邮箱：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % (user.username, active_url)
        self.send_mail(header, body, self.sender, [email])

    def send_verify_account(self, email, username, password):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash + '_email', email)
        cache.set(random_hash + '_username', username)
        cache.set(random_hash + '_password', password)
        active_url = 'https://gitshell.com/join/%s/' % random_hash
        header = u'[gitshell]注册邮件'
        body = u'尊敬的gitshell用户：\n感谢您选择了gitshell，请点击下面的地址激活您在gitshell的帐号：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
        self.send_mail(header, body, self.sender, [email])

    def send_resetpassword(self, user, email):
        random_hash = '%032x' % random.getrandbits(128)
        cache.set(random_hash, email)
        active_url = 'https://gitshell.com/resetpassword/%s/' % random_hash
        header = u'[gitshell]重置密码邮件'
        body = u'尊敬的 %s：\n如果您没有重置密码的请求，请忽略此邮件。点击下面的地址重置您在gitshell的帐号密码：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % (user.username, active_url)
        self.send_mail(header, body, self.sender, [email])



