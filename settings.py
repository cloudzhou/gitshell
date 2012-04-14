# Django settings for gitshell project.

DEBUG = True
TEMPLATE_DEBUG = True

ADMINS = (
    ('cloudzhou', 'cloudzhou@163.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gitshelldb',
        'USER': 'gitshell',
        'PASSWORD': '424953',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 1800,
    }
}
KEY_PREFIX = 'gs_'

TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'zh_CN'
DEFAULT_CHARSET = 'UTF-8'
SITE_ID = 1
USE_I18N = False
USE_L10N = True
MEDIA_ROOT = '/opt/gitshellstatic/static/media/'
MEDIA_URL = 'http://www.gitshell.com/static/media'
STATIC_ROOT = '/opt/gitshellstatic/static/'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
SESSION_COOKIE_AGE = 43200

STATICFILES_DIRS = (
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'git424953shell'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'gitshell.urls'

TEMPLATE_DIRS = (
    '/opt/8001/gitshell/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',
    'gitshell.index',
    'gitshell.keyauth',
    'gitshell.dist',
    'gitshell.keyvalue',
    # 'django.contrib.admin',
    # 'django.contrib.admindocs',
)

# See http://docs.djangoproject.com/en/dev/topics/logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/opt/run/var/log/gitshell.8001.log',
        },
    },
    'loggers': {
        'gitshell': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
