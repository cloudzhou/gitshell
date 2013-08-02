# -*- coding: utf-8 -*- 
#!/usr/bin/python
import os
import ConfigParser
from string import Template
import time
if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists('env.ini'):
        fr = None
        fw = None
        try:
            config = ConfigParser.RawConfigParser()
            config.readfp(open('env.ini'))
            items = dict(config.items('env'))
            items['timestamp'] = str(time.time())
            fr = open('settings.tmpl', 'r')
            fw = open('settings.py', 'w')
            properties_tmpl = fr.read()
            template = Template(properties_tmpl)
            fw.write(template.substitute(items))
        finally:
            if fr is not None:
                fr.close()
            if fw is not None:
                fw.close()

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
