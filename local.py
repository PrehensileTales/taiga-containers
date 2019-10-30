# -*- coding: utf-8 -*-
# https://github.com/taigaio/taiga-back/blob/master/settings/local.py.example
from .common import *
import environ

env = environ.Env()
DEBUG = env('DEBUG', cast=bool, default=False)
PUBLIC_REGISTER_ENABLED = env(
    'TAIGA_PUBLIC_REGISTER_ENABLED', cast=bool, default=True
)

SECRET_KEY = env('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', cast=list, default=['*'])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DJANGO_DB_NAME'),
        'USER': env('DJANGO_DB_USER'),
        'PASSWORD': env('DJANGO_DB_PASSWORD', default=""),
        'HOST': env('DJANGO_DB_HOST', default=""),
        'PORT': env('DJANGO_DB_PORT', default=""),
    }
}

TAIGA_HOSTNAME = env('TAIGA_HOSTNAME', default='localhost')

_HTTP = 'https' if env('TAIGA_SSL', cast=bool, default=False) else 'http'

SITES = {
    "api": {
       "scheme": _HTTP,
       "domain": TAIGA_HOSTNAME,
       "name": "api"
    },
    "front": {
      "scheme": _HTTP,
      "domain": TAIGA_HOSTNAME,
      "name": "front"
    },
}

SITE_ID = "api"

MEDIA_URL = "{}://{}/media/".format(_HTTP, TAIGA_HOSTNAME)
STATIC_URL = "{}://{}/static/".format(_HTTP, TAIGA_HOSTNAME)
MEDIA_ROOT = '/srv/taiga/media'
STATIC_ROOT = '/srv/taiga/static'

if env('OPENID_CLIENT_ID', default=None):
    INSTALLED_APPS += ["taiga_contrib_openid_auth"]
    OPENID_USER_URL = env('OPENID_USER_URL')
    OPENID_TOKEN_URL = env('OPENID_TOKEN_URL')
    OPENID_CLIENT_ID = env('OPENID_CLIENT_ID')
    OPENID_CLIENT_SECRET = env('OPENID_CLIENT_SECRET')

if env('TAIGA_EVENTS_HOST', default=None):
    EVENTS_PUSH_BACKEND = "taiga.events.backends.rabbitmq.EventsPushBackend"
    EVENTS_PUSH_BACKEND_OPTIONS = {"url": f"amqp://{env('RABBITMQ_DEFAULT_USER')}:{env('RABBITMQ_DEFAULT_PASS')}@{env('RABBITMQ_SERVER')}/{env('RABBITMQ_DEFAULT_VHOST')}"}

FEEDBACK_ENABLED = env('TAIGA_FEEDBACK_ENABLED', cast=bool, default=False)
if FEEDBACK_ENABLED:
    FEEDBACK_EMAIL = env('TAIGA_FEEDBACK_EMAIL')

# Async
# see celery_local.py
# BROKER_URL = 'amqp://taiga:taiga@rabbitmq:5672/taiga'

# see celery_local.py
CELERY_ENABLED = env('TAIGA_CELERY_ENABLED', cast=bool, default=False)

# Mail settings
#if env('USE_ANYMAIL', cast=bool, default=False):
#    INSTALLED_APPS += ['anymail']
#    ANYMAIL = {
#        "MAILGUN_API_KEY": env('ANYMAIL_MAILGUN_API_KEY'),
#    }
#    EMAIL_BACKEND = "anymail.backends.mailgun.MailgunBackend"
#    DEFAULT_FROM_EMAIL = "Taiga <{}>".format(env('DJANGO_DEFAULT_FROM_EMAIL'))

# Cache
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-snowflake"
#     }
# }
