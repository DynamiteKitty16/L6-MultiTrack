import os
import ssl
import certifi
import dj_database_url
from pathlib import Path
from decouple import config, Csv
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ENVIRONMENT VARIABLES
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', config('DJANGO_SECRET_KEY', default='fallback-insecure-key'))
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', config('EMAIL_HOST_USER'))
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', config('EMAIL_HOST_PASSWORD'))
EMAIL_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Database Configuration
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False  # Disable SSL for local SQLite
    )
}

# Session Security Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use database-backed sessions
SESSION_COOKIE_AGE = 1200  # 20 minutes to account for network delay on reauthenticate
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when browser closes
SESSION_COOKIE_SECURE = not DEBUG  # Secure cookies only in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookies

# Custom Session Timeout for Middleware
SESSION_TIMEOUT = 900  # 15 minutes


# Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'workspace',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'workspace.middleware.SessionTimeoutMiddleware',  # Handles timeout
    'workspace.middleware.UpdateLastActivityMiddleware',  # Tracks user activity
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'multi_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'workspace' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'workspace.context_processors.session_expiry',
            ],
        },
    },
]

WSGI_APPLICATION = 'multi_tracker.wsgi.application'

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'workspace.custom_validators.UppercaseValidator'},
    {'NAME': 'workspace.custom_validators.SpecialCharacterValidator'},
    {'NAME': 'workspace.custom_validators.NumberValidator'},
    {'NAME': 'workspace.custom_validators.NoReusePasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static and Media Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'workspace' / 'static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default Primary Key Field Type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Production Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
