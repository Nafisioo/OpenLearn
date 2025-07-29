# config/settings/base.py
import os
from pathlib import Path

import environ

# ─── 1) Project base directory ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── 2) Initialize django‑environ ─────────────────────────────────────────────
env = environ.Env(
    # set cast and default values
    DEBUG=(bool, False)
)

# ─── 3) Read .env file from project root ──────────────────────────────────────
env.read_env(os.path.join(BASE_DIR, '.env'))

# ─── 4) Core environment‑driven settings ──────────────────────────────────────
SECRET_KEY    = env('SECRET_KEY')
DEBUG         = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# ─── 5) Application definition ────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django contrib
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third‑party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # apps
    'accounts',
    'courses',
    'core',     # site feedback / categories
    'quizzes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # add your template dirs here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ─── 6) Database placeholder ───────────────────────────────────────────────────
# Actual DATABASES live in development.py and production.py
# DATABASES = env.db_url_config(default="sqlite:///db.sqlite3")

# ─── 7) Password validation ───────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

AUTH_USER_MODEL = 'accounts.User'

# ─── 8) Internationalization ──────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ─── 9) Static files ──────────────────────────────────────────────────────────
STATIC_URL = 'static/'

# ─── 10) Default primary key field type ───────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── 11) DRF & CORS ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
CORS_ALLOW_ALL_ORIGINS = True
