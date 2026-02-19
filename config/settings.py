"""
Django settings for config project.
Standard Production-Ready Configuration (Render + Azure).
"""

import os
from pathlib import Path
import environ
import ssl
from datetime import timedelta
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
import dj_database_url # ⚠️ تأكد من إضافته في requirements.txt

# 1. تهيئة البيئة
env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 🛡️ CORE SECURITY & ENVIRONMENT DETECTION
# ==============================================================================

# هل نحن في Azure؟
IN_AZURE_DEPLOYMENT = env.bool('IN_AZURE_DEPLOYMENT', False)
# هل نحن في Render؟ (Render يضيف هذا المتغير تلقائياً)
IN_RENDER_DEPLOYMENT = env.bool('RENDER', False)

DEBUG = env.bool('DJANGO_DEBUG', False)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='unsafe-secret-key-change-in-prod')
DB_ENCRYPTION_KEY = env('DB_ENCRYPTION_KEY', default='sEcret_Key_Must_Be_32_UrlSafe_Base64=')

ALLOWED_HOSTS = ["*"] # Render يدير النطاقات، * مقبولة أو ضع نطاقك الخاص

# ==============================================================================
# 🌐 INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = 'Europe/Oslo'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 🧩 APPS & MIDDLEWARE
# ==============================================================================

INSTALLED_APPS = [
    'daphne',
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'channels',
    'csp',
    'axes',
    'import_export',
    'apps.accounts',
    'apps.chat',
    'apps.core',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # ⚠️ مهم جداً لـ Render
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# 🗄️ DATABASE
# ==============================================================================

if IN_RENDER_DEPLOYMENT:
    # إعدادات قاعدة بيانات Render
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
else:
    # إعدادات التطوير المحلي أو Azure القديم
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='camp_medical_db'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='postgres'), 
            'HOST': env('DB_HOST', default='db'), # تم التعديل ليتناسب مع Docker
            'PORT': env('DB_PORT', default='5432'),
        }
    }

# ==============================================================================
# 🗄️ REDIS & CACHE
# ==============================================================================

REDIS_URL = env('REDIS_URL', default=None)

# إصلاح SSL في Azure و Render
if (IN_AZURE_DEPLOYMENT or IN_RENDER_DEPLOYMENT) and REDIS_URL and REDIS_URL.startswith('redis://'):
    # Render Redis لا يحتاج SSL عادةً داخل الشبكة الخاصة، لكن هذا الكود آمن
    pass 

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL], # Render يعطيك الرابط كاملاً
            },
        },
    }
    
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Render Redis (Internal) usually doesn't enforce SSL, removed strict SSL requirement
            }
        }
    }
    
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    # Local
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [("redis", 6379)]},
        },
    }
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"}
        }
    }
    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"

# ==============================================================================
# 🐇 CELERY SETTINGS
# ==============================================================================
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE 
CELERY_WORKER_CONCURRENCY = 2

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'epidemic-warning-every-15-minutes': {
        'task': 'apps.chat.tasks.check_epidemic_outbreak',
        'schedule': crontab(minute='*/15'), 
    },
    'gdpr-cleanup-every-day': {
        'task': 'apps.chat.tasks.delete_old_data',
        'schedule': crontab(hour=3, minute=0), 
    },
}

# ==============================================================================
# 🔒 AUTH & SECURITY
# ==============================================================================
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# ... (Validation & Axes Settings same as before) ...
AXES_FAILURE_LIMIT = 5          
AXES_COOLOFF_TIME = timedelta(minutes=10)     
AXES_RESET_ON_SUCCESS = True    
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_CLIENT_IP_CALLABLE = 'apps.core.utils.get_client_ip'

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# 🧠 AI SERVICES
# ==============================================================================
AZURE_TRANSLATOR_KEY = env('AZURE_TRANSLATOR_KEY', default='')
AZURE_TRANSLATOR_ENDPOINT = env('AZURE_TRANSLATOR_ENDPOINT', default='')
AZURE_TRANSLATOR_REGION = env('AZURE_TRANSLATOR_REGION', default='')
AZURE_OPENAI_ENDPOINT = env('AZURE_OPENAI_ENDPOINT', default='')
AZURE_OPENAI_KEY = env('AZURE_OPENAI_KEY', default='')
AZURE_OPENAI_DEPLOYMENT_NAME = env('AZURE_OPENAI_DEPLOYMENT_NAME', default='gpt-4o')

# ==============================================================================
# 🎨 STATIC & MEDIA & STORAGE
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# نستخدم Azure Blob للتخزين سواء كنا في Azure أو Render
if IN_AZURE_DEPLOYMENT or IN_RENDER_DEPLOYMENT:
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
    # تأكد من أن هذا المتغير موجود في Render Environment Variables
    MEDIA_URL = f"https://{env('AZURE_STORAGE_ACCOUNT_NAME', default='campmedia')}.blob.core.windows.net/media/"
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

UNFOLD = {
    # ... (Unfold settings same as before) ...
    "SITE_TITLE": "Medical Support System",
    "SITE_HEADER": "Camp Administration",
    "SITE_URL": "/auth/login/",
    # ...
}

# ==============================================================================
# 👮 CSP & Security
# ==============================================================================
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.onrender.com", # 🛑 السماح لنطاقات Render
        "https://*.azurecontainerapps.io",
    ]
)

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "data:", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https://www.gravatar.com", "https://*.blob.core.windows.net"],
        "connect-src": [
            "'self'",
            "ws://localhost:8000",
            "wss://*.onrender.com", # 🛑 السماح للويب سوكيت في Render
            "https://*.blob.core.windows.net",
            "https://*.openai.azure.com",
        ],
    }
}

if not DEBUG:
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