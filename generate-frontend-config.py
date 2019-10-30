#!/usr/bin/env python3
import json
python_home = '/srv/taiga/taiga-back/taiga'

activate_this = python_home + '/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

import environ

env = environ.Env()
_HTTP = 'https' if env('TAIGA_SSL', cast=bool, default=False) else 'http'
_WS = 'wss' if env('TAIGA_SSL', cast=bool, default=False) else 'ws'

config = {
    "api": f"{_HTTP}://{env('TAIGA_HOSTNAME', default='localhost')}/api/v1/",
    "eventsUrl": None,
    "eventsMaxMissedHeartbeats": 5,
    "eventsHeartbeatIntervalTime": 60000,
    "eventsReconnectTryInterval": 10000,
    "debug": env('DEBUG', cast=bool, default=False),
    "debugInfo": env('DEBUG', cast=bool, default=False),
    "defaultLanguage": env('TAIGA_DEFAULT_LANGUAGE', default="en"),
    "themes": ["taiga"],
    "defaultTheme": env('TAIGA_DEFAULT_THEME', default="taiga"),
    "publicRegisterEnabled": env('TAIGA_PUBLIC_REGISTER_ENABLED', cast=bool, default=True),
    "feedbackEnabled": env('TAIGA_FEEDBACK_ENABLED', cast=bool, default=False),
    "supportUrl": env('TAIGA_SUPPORT_URL', default=None),
    "privacyPolicyUrl": env('TAIGA_PRIVACY_POLICY_URL', default=None),
    "termsOfServiceUrl": env('TAIGA_TOS_URL', default=None),
    "GDPRUrl": env('TAIGA_GDPR_URL', default=None),
    "maxUploadFileSize": env('TAIGA_MAX_UPLOAD_FILE_SIZE', default=None),
    "tribeHost": None,
    "importers": [],
    "gravatar": env('TAIGA_GRAVATAR', cast=bool, default=False),
    "rtlLanguages": ["fa"],
    "contribPlugins": [ ]
}

if env('OPENID_CLIENT_ID', default=None):
    config['contribPlugins'].append('/plugins/openid-auth/openid-auth.json')
    config['openidAuth'] = env('OPENID_AUTH_URL')
    config['openidName'] = env('OPENID_LOGIN_NAME')
    config['openidClientId'] = env('OPENID_CLIENT_ID')

if env('TAIGA_EVENTS_HOST', default=None):
    config['eventsUrl'] = f"{_WS}://{env('TAIGA_HOSTNAME', default='localhost')}/events/"

print(json.dumps(config, sort_keys=True, indent=4, separators=(',', ': ')))
