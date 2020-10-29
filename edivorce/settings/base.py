"""
Django settings for this project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os

from django.urls import reverse_lazy
from environs import Env
from unipath import Path

env = Env()
env.read_env()  # read .env file, if it exists

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_DIR = Path(__file__).parent.parent
ENVIRONMENT = os.environ.get('ENVIRONMENT_TYPE', 'localdev')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# The SECRET_KEY is provided via an environment variable in OpenShift
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    default='9e4@&tw46$l31)zrqe3wi+-slqm(ruvz&se0^%9#6(_w3ui!c0'
)

DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'mozilla_django_oidc',  # Load after auth
    'rest_framework',
    'debug_toolbar',
    'corsheaders',
    'edivorce.apps.core',
    'compressor',
    'crispy_forms',
    'sass_processor',
    'graphene_django',
)

# add the POC app only if applicable
if ENVIRONMENT in ['localdev', 'dev', 'test']:
    INSTALLED_APPS += (
        'edivorce.apps.poc',
    )

MIDDLEWARE = (
    'edivorce.apps.core.middleware.basicauth_middleware.BasicAuthMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

AUTH_USER_MODEL = 'core.BceidUser'

AUTHENTICATION_BACKENDS = (
    'edivorce.apps.core.middleware.keycloak.EDivorceKeycloakBackend',
)

ROOT_URLCONF = 'edivorce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['edivorce/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'edivorce.apps.core.context_processors.settings_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# need to disable auth in Django Rest Framework so it doesn't get triggered
# by presence of Basic Auth headers
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ]
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_TZ = True
TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True
USE_THOUSANDS_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

BCGOV_NETWORK = os.environ.get('PROXY_NETWORK', '0.0.0.0/0')

FORCE_SCRIPT_NAME = '/'

FIXTURE_DIRS = (
    os.path.join(PROJECT_ROOT, 'edivorce', 'fixtures'),
)

BASICAUTH_ENABLED = False

# Google Tag Manager (dev/test instance)
GTM_ID = 'GTM-NJLR7LT'


def show_toolbar(request):
    return ENVIRONMENT in ['localdev', 'dev']


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    'SHOW_COLLAPSED': True,
}

SECURE_BROWSER_XSS_FILTER = True

# eFiling Hub settings
EFILING_HUB_ENABLED = False
EFILING_HUB_TOKEN_BASE_URL = env('EFILING_HUB_TOKEN_BASE_URL', '')
EFILING_HUB_REALM = env('EFILING_HUB_REALM', '')
EFILING_HUB_CLIENT_ID = env('EFILING_HUB_CLIENT_ID', '')
EFILING_HUB_CLIENT_SECRET = env('EFILING_HUB_CLIENT_SECRET', '')
EFILING_HUB_API_BASE_URL = env('EFILING_HUB_API_BASE_URL', '')

EFILING_BCEID = env('EFILING_BCEID', '', subcast=str)

# Keycloak OpenID Connect settings
# Provided by mozilla-django-oidc
LOGIN_URL = reverse_lazy('oidc_authentication_init')
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_RP_SCOPES = 'openid email profile'
# this is needed to bypass the Keycloak login screen
OIDC_AUTH_REQUEST_EXTRA_PARAMS = {'kc_idp_hint': 'bceid'}
OIDC_RP_CLIENT_SECRET = env('KEYCLOAK_CLIENT_SECRET', '')
OIDC_OP_LOGOUT_URL_METHOD = 'edivorce.apps.core.middleware.keycloak.keycloak_logout'

VIRTUAL_SWEARING_ENABLED = False
