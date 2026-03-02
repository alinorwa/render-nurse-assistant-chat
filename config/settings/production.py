"""
config/settings/production.py
Settings for production environment (Render).
"""
import ssl
import dj_database_url
from .base import *

# 1. Security
DEBUG = False
SECRET_KEY = env('SECRET_KEY') # يجب أن يأتي من متغيرات Render
DB_ENCRYPTION_KEY = env('DB_ENCRYPTION_KEY')

ALLOWED_HOSTS = ["*"] # Render يدير النطاقات، ويمكنك تحديد نطاقك الخاص هنا

# 2. Database (Render Postgres)
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=False)
}

# 3. Redis (Render Redis)
REDIS_URL = env('REDIS_URL')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# 4. Email (Gmail SMTP)
EMAIL_BACKEND = 'apps.core.email_backend.IPv4EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_TIMEOUT = 30
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 5. Azure Blob Storage (Media Files)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "account_name": env('AZURE_STORAGE_ACCOUNT_NAME'),
            "account_key": env('AZURE_STORAGE_ACCOUNT_KEY'),
            "azure_container": "media",
            "expiration_secs": None,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
MEDIA_URL = f"https://{env('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/media/"

# 6. Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True