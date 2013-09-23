# -*- coding: utf-8 -*-
import os, re, pipes, sys, traceback, codecs
import time, json, hashlib, shutil
from django.core.cache import cache
from gitshell.objectscache.models import CacheKey
from gitshell.gsuser.models import GsuserManager
from gitshell.settings import logger

class UrlRouter():

    def __init__(self, userprofile, context_username):
        self.userprofile = userprofile
        self.context_username = context_username

    def route(self, url):
        if not self.userprofile or not self.userprofile.id or not self.userprofile.current_user_id:
            return url
        if self.userprofile.current_user_id == 0 or self.userprofile.id == self.userprofile.current_user_id:
            return url
        current_user = GsuserManager.get_user_by_id(self.userprofile.current_user_id)
        if current_user:
            return '/%s/-%s' % (current_user.username, url)
        return url

    def route_context(self, url):
        if self.context_username and self.context_username != '':
            return '/%s/-%s' % (self.context_username, url)
        return url

