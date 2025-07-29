from .base import *

# In development we want verbose errors and the local SQLite DB
DEBUG = True

# SQLite by default
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# Allow localhost in dev
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
