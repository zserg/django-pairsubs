#!/usr/bin/env python
import os
import sys
import warnings
from optparse import OptionParser

import django
from django.conf import settings
from django.core.management import call_command


def runtests(test_path='tests'):
    if not settings.configured:
        # Choose database for settings
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        }
        test_db = os.environ.get('DB', 'sqlite')
        if test_db == 'mysql':
            DATABASES['default'].update({
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'test',
                'USER': 'root',
            })
        elif test_db == 'postgres':
            DATABASES['default'].update({
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'NAME': 'test',
            })

        # Configure test environment
        settings.configure(
            DATABASES=DATABASES,
	    DEBUG=True,
            INSTALLED_APPS=(
		'django.contrib.admin',
		'django.contrib.auth',
		'django.contrib.contenttypes',
		'django.contrib.sessions',
		'django.contrib.messages',
		'django.contrib.staticfiles',
		'pairsubs',
            ),
            ROOT_URLCONF='tests.urls',
            LANGUAGES=(
                ('en', 'English'),
            ),
            MIDDLEWARE_CLASSES=(
	    'django.middleware.security.SecurityMiddleware',
	    'django.contrib.sessions.middleware.SessionMiddleware',
	    'django.middleware.common.CommonMiddleware',
	    'django.middleware.csrf.CsrfViewMiddleware',
	    'django.contrib.auth.middleware.AuthenticationMiddleware',
	    'django.contrib.messages.middleware.MessageMiddleware',
	    'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
)


    django.setup()
    warnings.simplefilter('always', DeprecationWarning)
    failures = call_command(
        'test', test_path, interactive=False, failfast=False, verbosity=2)

    sys.exit(bool(failures))


if __name__ == '__main__':
    parser = OptionParser()

    (options, args) = parser.parse_args()
runtests(*args)

