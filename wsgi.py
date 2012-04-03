import os
import sys
import django.core.handlers.wsgi

#sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gitshell.settings")
application = django.core.handlers.wsgi.WSGIHandler()

