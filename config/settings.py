"""
Django settings for config project.
Standard Production-Ready Configuration (Optimized for Azure).
"""

import os
from pathlib import Path
import environ
import ssl
from datetime import timedelta
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# 1. تهيئة البيئة
# 1. Environment Setup
env = environ.Env()
# قراءة ملف .env إذا وجد (للتطوير المحلي)
# Read .env file if exists (for local development)
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 🛡️ CORE SECURITY
# ==============================================================================

# يجب أن يكون False في Azure (نقوم بضبطه عبر متغير بيئة في Azure Portal)
# Must be False in Azure (set via env var in Azure Portal)
DEBUG = env.bool('DJANGO_DEBUG', False)

# هل نحن في Azure؟ (نقوم بضبط هذا المتغير في Azure Portal)
# Are we in Azure? (Set this variable in Azure Portal)
IN_AZURE_DEPLOYMENT = env.bool('IN_AZURE_DEPLOYMENT', False)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='unsafe-secret-key-change-in-prod')
DB_ENCRYPTION_KEY = env('DB_ENCRYPTION_KEY', default='sEcret_Key_Must_Be_32_UrlSafe_Base64=')

# السماح لجميع النطاقات (لأن Azure Load Balancer يقف أمامنا)
# Allow all hosts (since Azure Load Balancer is in front)
ALLOWED_HOSTS = ["*"]

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
    'daphne', # ASGI Server
    
    # UI Theme
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",

    # Django Core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third Party
    'channels',
    'csp',
    'axes',
    'import_export',
    
    # Local Apps
    'apps.accounts',
    'apps.chat',
    'apps.core',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # لملفات الستاتيك / For static files
    "csp.middleware.CSPMiddleware",               # حماية المحتوى / Content protection
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",             # حماية الدخول / Login protection
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# 🗄️ DATABASE
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='camp_medical_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD',), 
        'HOST': env('DB_HOST', default='host.docker.internal'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# ==============================================================================
# 🗄️ REDIS & CACHE (With SSL Fix)
# ==============================================================================

REDIS_URL = env('REDIS_URL', default=None)

# Force SSL scheme for Azure Redis if not present
if IN_AZURE_DEPLOYMENT and REDIS_URL and REDIS_URL.startswith('redis://'):
    REDIS_URL = REDIS_URL.replace('redis://', 'rediss://', 1)


if REDIS_URL:
    # --- إعدادات الإنتاج (Azure) ---
    # --- Production Settings (Azure) ---
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [
                    {
                        "address": REDIS_URL,
                        "ssl_cert_reqs": ssl.CERT_NONE,  # 🛑 الحل لمشاكل الاتصال في Azure / Solution for connection issues in Azure
                    }
                ],
                "capacity": 1500,
                "expiry": 10,
            },
        },
    }
    
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": ssl.CERT_NONE},
            }
        }
    }
    
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}

else:
    # --- إعدادات التطوير المحلي ---
    # --- Local Development Settings ---
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

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

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
AZURE_TRANSLATOR_KEY = env('AZURE_TRANSLATOR_KEY')
AZURE_TRANSLATOR_ENDPOINT = env('AZURE_TRANSLATOR_ENDPOINT')
AZURE_TRANSLATOR_REGION = env('AZURE_TRANSLATOR_REGION')

AZURE_OPENAI_ENDPOINT = env('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = env('AZURE_OPENAI_KEY')
AZURE_OPENAI_DEPLOYMENT_NAME = env('AZURE_OPENAI_DEPLOYMENT_NAME', default='gpt-4o')
                                     

# ==============================================================================
# 🎨 STATIC & MEDIA & STORAGE
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'



if IN_AZURE_DEPLOYMENT:
    # --- إعدادات التخزين السحابي (Azure Blob) ---
    # --- Cloud Storage Settings (Azure Blob) ---
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
else:
    # --- إعدادات التخزين المحلي ---
    # --- Local Storage Settings ---
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

# إعدادات Unfold
# Unfold Settings
UNFOLD = {
    "SITE_TITLE": "Medical Support System",
    "SITE_HEADER": "Camp Administration",
    "SITE_URL": "/auth/login/",
    "COLORS": {
        "primary": {
            "50": "240 253 250",
            "100": "204 251 241",
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "20 184 166",
            "600": "13 148 136",
            "700": "15 118 110",
            "800": "17 94 89",
            "900": "19 78 74",
            "950": "4 47 46",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Overview"),
                "separator": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("custom_dashboard"),
                    },
                ],
            },
            {
                "title": _("Medical Operations"),
                "separator": True,
                "items": [
                    {
                        "title": _("Live Chat"),
                        "icon": "forum",
                        "link": reverse_lazy("admin:chat_chatsession_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": _("Epidemic Alerts"),
                        "icon": "coronavirus",
                        "link": reverse_lazy("admin:chat_epidemicalert_changelist"),
                    },
                    {
                        "title": _("Emergency Keywords"),
                        "icon": "warning",
                        "link": reverse_lazy("admin:chat_dangerkeyword_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Staff"),
                "separator": True,
                "items": [
                    {
                        "title": _("Refugees & Nurses"),
                        "icon": "group",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                ],
            },
        ],
    },
    "STYLES": [lambda request: static("css/admin_sticky.css")],
}

# ==============================================================================
# 👮 CSP & Security (Web Focused)
# ==============================================================================

# السماح للنطاقات الحقيقية في Azure
# Allow real domains in Azure
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.azurecontainerapps.io",
        # أضف رابطك الدقيق لزيادة التأكيد
        # Add your exact URL for extra confirmation
        "https://camp-web.graymushroom-26f94677.norwayeast.azurecontainerapps.io",
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
            "ws://127.0.0.1:8000",
              # السماح العام والخاص
              # General and specific allowance
            "wss://*.azurecontainerapps.io",
            "wss://camp-web.graymushroom-26f94677.norwayeast.azurecontainerapps.io", # للسماح بالويب سوكيت في Azure
            "https://camp-web.graymushroom-26f94677.norwayeast.azurecontainerapps.io", # للسماح بالويب سوكيت في Azure
             # أضفنا هذا السطر للسماح بجلب الصور عبر JS و Service Worker
            # Added this line to allow fetching images via JS and Service Worker
            "https://*.blob.core.windows.net",
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