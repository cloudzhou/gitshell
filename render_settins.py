# -*- coding: utf-8 -*- 
#!/usr/bin/python
import os, sys
import ConfigParser
from string import Template
import time
if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists('env.ini'):
        print 'can not found env.ini, exit now'
        sys.exit(128)
    config = ConfigParser.RawConfigParser()
    with open('env.ini', 'r') as envF, open('settings.tmpl', 'r') as tmplF, open('settings.py', 'w') as settingsF:
        config.readfp(envF)
        items = dict(config.items('env'))
        items['timestamp'] = str(time.time())
        properties_tmpl = tmplF.read()
        template = Template(properties_tmpl)
        settingsF.write(template.substitute(items))

########### env.ini ###########
"""
[env]
debug = True
template_debug = True
user = git
password = gitshell
host = 127.0.0.1
template_dirs = /opt/app/8001/gitshell/templates
logging_file_path = /opt/run/var/log/gitshell.8001.log
secret_key = ''
github_client_id = ''
github_client_secret = ''
dropbox_app_key = ''
dropbox_app_secret = ''
dropbox_access_token = ''
dropbox_access_token_secret = ''
"""
