# Django settings for learnscripture project.

import socket
import sys
import os
import json

hostname = socket.gethostname()
DEVBOX = ('webfaction' not in hostname)
LIVEBOX = not DEVBOX
DEBUG = DEVBOX
TEMPLATE_DEBUG = DEBUG

# A kitten gets killed every time you use this:
TESTING = 'manage.py test' in ' '.join(sys.argv)

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ../
PROJECT_DIR = os.path.dirname(SRC_DIR)
WEBAPP_DIR = os.path.dirname(PROJECT_DIR)
HOME_DIR = os.environ['HOME']

secrets = json.load(open(os.path.join(SRC_DIR, "config", "secrets.json")))

# At least some passwords need to be bytes, not unicode objects
secrets = dict([(k, s if not isinstance(s, unicode) else s.encode('ascii')) for k, s in secrets.items()])

if LIVEBOX:
    p = os.path.dirname(os.path.abspath(__file__))
    PRODUCTION = "webapps/learnscripture_django/" in p
    STAGING = "webapps/learnscripture_staging_django/" in p

    assert not (PRODUCTION and STAGING)

    EMAIL_HOST = secrets['EMAIL_HOST']
    EMAIL_HOST_USER = secrets['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = secrets['EMAIL_HOST_PASSWORD']

    if PRODUCTION:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': secrets["PRODUCTION_DB_NAME"],
                'USER': secrets["PRODUCTION_DB_USER"],
                'PASSWORD': secrets["PRODUCTION_DB_PASSWORD"],
                'HOST': 'localhost',
                'PORT': secrets["PRODUCTION_DB_PORT"],
                'ATOMIC_REQUESTS': True,
                }
            }
        SECRET_KEY = secrets["PRODUCTION_SECRET_KEY"]
        SENTRY_DSN = secrets["PRODUCTION_SENTRY_DSN"]

    elif STAGING:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': secrets["STAGING_DB_NAME"],
                'USER': secrets["STAGING_DB_USER"],
                'PASSWORD': secrets["STAGING_DB_PASSWORD"],
                'HOST': 'localhost',
                'PORT': secrets["STAGING_DB_PORT"],
                'ATOMIC_REQUESTS': True,
                }
            }
        SECRET_KEY = secrets["STAGING_SECRET_KEY"]
        SENTRY_DSN = secrets["STAGING_SENTRY_DSN"]
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture',
            'USER': 'learnscripture',
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': '5432',
            'ATOMIC_REQUESTS': True,
        }
    }

    # For e-mail testing, run:
    #  fakemail.py --path=/home/luke/devel/learnscripture.net/tests/mail --background
    EMAIL_HOST = 'localhost'
    EMAIL_HOST_USER = None
    EMAIL_HOST_PASSWORD = None
    EMAIL_PORT = 8025

    SECRET_KEY = secrets['DEVELOPMENT_SECRET_KEY']
    SENTRY_DSN = secrets["DEVELOPMENT_SENTRY_DSN"]

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    PRODUCTION = STAGING = False


AUTH_USER_MODEL = 'accounts.Account'

SESSION_COOKIE_AGE = 3600 * 24 * 31 * 4 # 4 months

ADMINS = [
    ('', 'admin@learnscripture.net')
]

MANAGERS = ADMINS

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

SERVER_EMAIL = 'website@learnscripture.net'
DEFAULT_FROM_EMAIL = 'luke@learnscripture.net'
CONTACT_EMAIL = 'contact@learnscripture.net'


if DEVBOX or STAGING:
    PAYPAL_RECEIVER_EMAIL = 'paypal_1314646057_biz@cciw.co.uk'
    PAYPAL_TEST = True
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@learnscripture.net"
    PAYPAL_TEST = False
PAYPAL_IMAGE = "https://www.paypalobjects.com/en_US/GB/i/btn/btn_buynowCC_LG.gif"


TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

USE_I18N = False
USE_L10N = False
USE_TZ = True

if LIVEBOX:
    if PRODUCTION:
        MEDIA_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_usermedia')
        STATIC_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_static')
    elif STAGING:
        MEDIA_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_staging_usermedia')
        STATIC_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_staging_static')

else:
    MEDIA_ROOT = os.path.join(PROJECT_DIR, 'usermedia')
    STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

MEDIA_URL = '/usermedia/'
STATIC_URL = '/static/'

STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

LOGIN_URL = '/admin/'

CSRF_FAILURE_VIEW = 'learnscripture.views.csrf_failure'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    m for b, m in
    [
        (DEBUG, 'debug_toolbar.middleware.DebugToolbarMiddleware'),
        (True, 'learnscripture.middleware.StatsMiddleware'),
        (True, 'django.middleware.common.CommonMiddleware'),
        (True, 'django.contrib.sessions.middleware.SessionMiddleware'),
        (True, 'django.middleware.csrf.CsrfViewMiddleware'),
        (True, 'django.contrib.auth.middleware.AuthenticationMiddleware'),
        (True, 'django.contrib.messages.middleware.MessageMiddleware'),
        (True, 'django.middleware.clickjacking.XFrameOptionsMiddleware'),
        (PRODUCTION, 'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware'),
        (DEVBOX, 'learnscripture.middleware.DebugMiddleware'),
        (DEBUG or STAGING, 'learnscripture.middleware.PaypalDebugMiddleware'),
        (True, 'learnscripture.middleware.IdentityMiddleware'),
        (True, 'pagination.middleware.PaginationMiddleware'),
        (True, 'fiber.middleware.AdminPageMiddleware'),
    ]
    if b
]


TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.i18n',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'learnscripture.context_processors.session_forms',
    'learnscripture.context_processors.referral_links',
    'learnscripture.context_processors.menu',
    'learnscripture.context_processors.notices',
    'learnscripture.context_processors.theme_fonts',
    'learnscripture.context_processors.settings_processor',
    'learnscripture.context_processors.request_account',
]

ROOT_URLCONF = 'learnscripture.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'learnscripture.wsgi.application'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',
    'south',
    # This project
    'learnscripture',
    'bibleverses',
    'accounts',
    'scores',
    'payments',
    'awards',
    'events',
    'groups',
    'comments',
    # Third party
    'piston',
    'mptt',
    'compressor',
    'fiber',
    'bootstrapform',
    'pagination',
    'raven.contrib.django.raven_compat',
    'spurl',
    'paypal.standard.ipn',
    'app_metrics',
    'selectable',
    'rstify',
    'kombu.transport.django',
    'django_markup',
]

ALLOWED_HOSTS = [".learnscripture.net"]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'learnscripture': {
            'level': 'INFO',
            'handlers': ['sentry'],
            'propagate': False,
            },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'celery': {
            'level': 'WARNING',
            'handlers': ['sentry'],
            'propagate': False,
        },
    },
}

FIBER_DEFAULT_TEMPLATE = 'fiber_singlecol.html'
FIBER_TEMPLATE_CHOICES = [(FIBER_DEFAULT_TEMPLATE, 'Single column')]



PISTON_DISPLAY_ERRORS = False


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    }

CACHES = {
    'default': {
        'BACKEND': 'caching.backends.memcached.CacheClass',
        'LOCATION': 'unix:%s/memcached.sock' % HOME_DIR,
        'KEY_PREFIX': 'learnscripture.net' if PRODUCTION else 'staging.learnscripture.net'
    }
} if LIVEBOX else {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
}

if DEVBOX:
    CACHE_PREFIX = 'ls1'
else:
    if PRODUCTION:
        CACHE_PREFIX = 'ls1'
    else:
        CACHE_PREFIX = 'ls2'

if TESTING:
    # Caching count() seems to cause errors in test suite
    CACHE_COUNT_TIMEOUT = 0

    # speed up tests:
    INSTALLED_APPS = [a for a in INSTALLED_APPS
                      if a != 'south']


else:
    CACHE_COUNT_TIMEOUT = 60

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'raw_enabled': False,
    'file_insertion_enabled': False,
}

MARKUP_SETTINGS = {
    'restructuredtext': {
        'settings_overrides': RESTRUCTUREDTEXT_FILTER_SETTINGS,
    }
}

CAMPAIGN_CONTEXT_PROCESSORS = [
    'learnscripture.context_processors.campaign_context_processor'
]

### Raven

RAVEN_CONFIG = {
    'dsn': SENTRY_DSN,
}

### Celery ###

BROKER_URL = 'django://'

if TESTING or DEVBOX:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

CELERYD_CONCURRENCY = 1

CELERY_RESULT_BACKEND = 'disabled'


### LearnScripture.net specific settings ###

IDENTITY_EXPIRES_DAYS = 22

MINIMUM_PASSWORD_LENGTH = 6

REQUIRE_SUBSCRIPTION = False

ESV_API_KEY = 'IP'

if PRODUCTION:
    GOOGLE_ANALYTICS_ACCOUNT = "UA-29644888-1"
else:
    GOOGLE_ANALYTICS_ACCOUNT = None
