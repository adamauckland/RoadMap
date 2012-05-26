# Django settings for roadmap project.
import os, sys
import django
import socket


# calculated paths for django and the site
# used as starting points for various other paths
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

hostname = 'settings_' + socket.gethostname().replace('.','_') + '_initialise'
hostpath = os.path.join(os.path.abspath('.'), hostname + '.py')

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('Nobody', ''),
)

MANAGERS = ADMINS

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')
MEDIA_URL = '/media/'

SECRET_KEY = 'CHANGE_THIS'


DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': os.path.join(SITE_ROOT, 'db.sql'),
		'USER': '',
		'PASSWORD': '',
		'HOST': '',
		'PORT': '',
	}
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jnfdgjiudfhbiudvnoivdfkvncieuhrefiejrbgjdkfb'

# List of callables that know how to import templates from various sources.


if DEBUG:
	TEMPLATE_LOADERS = (
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
		'django.template.loaders.eggs.Loader',
	)
else:
	TEMPLATE_LOADERS = (
		('django.template.loaders.cached.Loader', (
			'django.template.loaders.filesystem.Loader',
			'django.template.loaders.app_directories.Loader',
		)),
	)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.debug',
	'django.contrib.auth.context_processors.auth',
	'djangoflash.context_processors.flash',

	'roadmap.ledger.context_processor.user_details',
	'roadmap.ledger.context_processor.notifications',
	'roadmap.ledger.context_processor.get_current_path',

	'django.core.context_processors.media',

)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'djangoflash.middleware.FlashMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',

	'reversion.middleware.RevisionMiddleware',
	
	'roadmap.ledger.middleware.MediaCacheHeaders',
	'roadmap.ledger.middleware.MultipleProxyMiddleware',

)

ROOT_URLCONF = 'roadmap.urls'

TEMPLATE_DIRS = (
	os.path.join(SITE_ROOT, 'templates')
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'tagging',
	'roadmap.ledger',
	'tinymce',
	'reversion',
	'django.contrib.admin',
	'django.contrib.markup',
	'roadmap.chat',
	'south',
	'avatar',
	'haystack',
)
CHAT_ROOT = os.path.join(MEDIA_ROOT, 'chat')

AUTH_PROFILE_MODULE = 'roadmap.ledger.UserProfile'

FLASH_IGNORE_MEDIA = True # Optional. Default: DEBUG
FLASH_STORAGE = 'session' # Optional

LOGIN_REDIRECT_URL = '/roadmap/ledger/login'

MAX_TAG_LENGTH = 500
FORCE_LOWERCASE_TAGS = True

#
# RoadMap
#
ROADMAP_EMAIL_EMAIL = ''
ROADMAP_EMAIL_USERNAME = ''
ROADMAP_EMAIL_PASSWORD = ''
ROADMAP_EMAIL_SERVER = ''

#
# TinyMCE is used for the HTML editor
#
TINYMCE_JS_URL = '/media/layout/tiny_mce/tiny_mce.js'
TINYMCE_JS_ROOT = os.path.join(MEDIA_ROOT, 'layout', 'tiny_mce')
TINYMCE_DEFAULT_CONFIG = {
	'plugins': "table,spellchecker,paste,searchreplace",
	'theme': "simple",
}

AVATAR_STORAGE_DIR = os.path.join(SITE_ROOT, 'media', 'uploads')

#
# Haystack search configuration
#
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(SITE_ROOT, 'media', 'site_index')
HAYSTACK_SITECONF = 'roadmap.search_sites'

HAYSTACK_CONNECTIONS = {
	'default': {
		'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
		'PATH': os.path.join(SITE_ROOT, 'media', 'site_index'),
		'INCLUDE_SPELLING': True,
	}
}

INTERNAL_IPS = (
)

PROFILE_LOG_BASE = os.path.join(SITE_ROOT, 'profile')

SESSION_COOKIE_AGE = (3600) * 2

try:
	from localsettings import *
except ImportError:
	pass