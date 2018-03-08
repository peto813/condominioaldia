"""
Django settings for condominioaldia project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
from django.conf import settings

if settings.DEBUG == False:
    import sys, decimal
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import os
    from django.utils.translation import ugettext_lazy as _
    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'ihs56*r+bd)phn1db3)y7%m@0p7t)6u2esuff+p%_!r6-znz7^'

    # SECURITY WARNING: don't run with debug turned on in production!
    #DEBUG = False

    ALLOWED_HOSTS = ['peto813.webfactional.com', 'www.condominioaldia.net', 'condominioaldia.net']

    # Application definition

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.humanize',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'condominioaldia_app',
        'rest_framework',
        'rest_framework.authtoken',
        'rest_auth',
        'django_filters',
        'django.contrib.sites',
        'allauth',
        'allauth.account',
        'rest_auth.registration',
        'easy_pdf'
    ]

    SITE_ID = 1

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'condominioaldia_app.middleware.CondoStatusResponseMiddleware'
    ]

    ROOT_URLCONF = 'condominioaldia.urls'


    #PROJECT EMAIL SETTINGS
    DEFAULT_FROM_EMAIL = 'webmaster@condominioaldia.net'
    SERVER_EMAIL = 'webmaster@condominioaldia.net'
    EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
    EMAIL_HOST_USER = 'AKIAI5S5NY4UBMENXNEQ'
    EMAIL_HOST_PASSWORD = 'Ak46G+GxuY39tHG9TjZA3xuDEnt8pTDNy7ie/eL/kDsr'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    ADMINS = (('Einstein Millan', 'peto813@gmail.com'), ('Einstein Millan', 'peto813@hotmail.com'))

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(BASE_DIR, 'templates'),
                os.path.join(BASE_DIR, 'templates', 'admin','condominioaldia_app')
            ],
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

    WSGI_APPLICATION = 'condominioaldia.wsgi.application'


    # Database
    # https://docs.djangoproject.com/en/1.11/ref/settings/#databases
    #condominioaldia_db
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'condominioaldia_db',
            'USER': 'peto813',
            'PASSWORD': 'ou63ut14',
            #'HOST': '127.0.0.1',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #     }
    # }


    # Password validation
    # https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]


    # Internationalization
    # https://docs.djangoproject.com/en/1.11/topics/i18n/

    LANGUAGE_CODE = 'es'

    TIME_ZONE = 'America/Caracas'

    USE_I18N = True

    USE_L10N = True

    USE_TZ = True


    LANGUAGES = (
        ('en', _('English')),
        ('pt-br', _('Portuguese')),
        ('it', _('Italian')),
        ('fr', _('French')),
        ('es', _('Spanish')),
    )


    LOCALE_PATHS = (
        os.path.join(BASE_DIR, 'conf/locale'),
    )
    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.11/howto/static-files/


    STATIC_URL = 'https://www.condominioaldia.net/static/'
    STATIC_ROOT='/home/peto813/webapps/condominioaldia_static/'

            #Th absolute path to the directory where collectstatic will collect static files for deployment.
    STATICFILES_DIRS =('/home/peto813/webapps/condominioaldia/condominioaldia/static/project_static/',)


    MEDIA_URL = 'https://www.condominioaldia.net/media/'
    MEDIA_ROOT = '/home/peto813/webapps/condominioaldia_media/'
    # these two have to do with end-users (whatever is being uploaded) 


    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': (
            'django_filters.rest_framework.DjangoFilterBackend',
      
        ),
        # Use Django's standard `django.contrib.auth` permissions,
        # or allow read-only access for unauthenticated users.
        # 'DEFAULT_PARSER_CLASSES': (
        #     'rest_framework.parsers.JSONParser',
        # ),


        'DEFAULT_RENDERER_CLASSES' : (
            'rest_framework.renderers.JSONRenderer',
            #'rest_framework.renderers.BrowsableAPIRenderer',
        ),

        'DEFAULT_AUTHENTICATION_CLASSES': (
            # 'rest_framework.authentication.BasicAuthentication',
            # 'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': [
            #'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
            #'rest_framework.permissions.DjangoModelPermissions'
            #'rest_framework.permissions.IsAuthenticatedOrReadOnly',
            #'rest_framework.permissions.IsAuthenticated'
            'rest_framework.permissions.AllowAny'

        ]
    }

    #ALLAUTH SETTINGS

    #ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_AUTHENTICATION_METHOD = 'email'
    ACCOUNT_ADAPTER = 'condominioaldia_app.custom_adapters.condominioaldiaAccountAdapter'
    ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
    ACCOUNT_EMAIL_VERIFICATION ='mandatory'
    ACCOUNT_SIGNUP_FORM_CLASS = 'condominioaldia_app.serializers.registroSerializer'
    ACCOUNT_UNIQUE_EMAIL = True
    ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
    ACCOUNT_CONFIRM_EMAIL_ON_GET = True

    #ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
    ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 1800
    ACCOUNT_EMAIL_CONFIRMATION_HMAC = False#SETTING THIS TO 'TRUE' TURNS OFF EMAIL VERIFICATION COOLDOWN

    AUTHENTICATION_BACKENDS = (
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',

        # `allauth` specific authentication methods, such as login by e-mail
        'allauth.account.auth_backends.AuthenticationBackend',
    )

    #CELERY SETTINGS
    CELERY_IGNORE_RESULT = True
    CELERY_IMPORTS = ['condominioaldia_app.tasks']


    #CONDOMINIOALDIA_APP SETTINGS
    MINIMA_ALICUOTA  = '99.75'
    COMISSION = 0.01
    TWOPLACES = decimal.Decimal(10) ** -2 

    #REST AUTH SETTINGS
    OLD_PASSWORD_FIELD_ENABLED = True

    #HTTPS SETTINGS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    HTTP_PROTOCOL = 'https'