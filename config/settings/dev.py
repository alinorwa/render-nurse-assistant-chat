"""
config/settings/dev.py
Settings for local development (Docker Local).
"""
from .base import *

# 1. Debugging
DEBUG = True
SECRET_KEY = env('DJANGO_SECRET_KEY', default='unsafe-local-dev-key')
DB_ENCRYPTION_KEY = env('DB_ENCRYPTION_KEY', default='unsafe-local-enc-key')

ALLOWED_HOSTS = ["*"]

# 2. Database (Local Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='camp_medical_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='db'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# 3. Redis (Local)
REDIS_URL = env('REDIS_URL', default='redis://redis:6379/0')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"}
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# 4. Email (Gmail or Console)
# محلياً يمكنك الاختيار عبر ملف .env
USE_REAL_EMAIL = env.bool('USE_REAL_EMAIL', default=False)

if USE_REAL_EMAIL:
    EMAIL_BACKEND = 'apps.core.email_backend.IPv4EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 5. Local Storage (Faster for dev)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'