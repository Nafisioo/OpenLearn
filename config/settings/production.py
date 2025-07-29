from .base import env, BASE_DIR
from .base import *

# In production DEBUG is always off
DEBUG = False

# Expect DATABASE_URL in your environment, e.g.
# postgres://USER:PASSWORD@HOST:PORT/DBNAME
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# Fill ALLOWED_HOSTS from env or fallback to your real domain(s)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Security hardening
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Example: Use WhiteNoise for static files (if you add it)
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'whitenoise.middleware.WhiteNoiseMiddleware'
)
STATIC_ROOT = BASE_DIR / 'staticfiles'
