import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append('/Library/Python/2.7/site-packages')
sys.path.append('/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python')
print sys.path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gitshell.settings")
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

