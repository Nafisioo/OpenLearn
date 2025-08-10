from .base import *


DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# SQLite by default
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

