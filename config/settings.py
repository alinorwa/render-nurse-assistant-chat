"""
Django settings for config project.
Standard Production-Ready Configuration (Render + Azure + Local Docker).
"""

import os
from pathlib import Path
import environ
import ssl
from datetime import timedelta
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
import dj_database_url 

# 1. تهيئة البيئة
env = environ.Env()
# قراءة ملف .env إذا وجد (للتطوير المحلي)
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 🛡️ CORE SECURITY & ENVIRONMENT DETECTION
# ==============================================================================

# هل نحن في Render؟ (Render يضيف هذا المتغير تلقائياً)
IN_RENDER_DEPLOYMENT = env.bool('RENDER', False)

# تفعيل وضع التصحيح فقط إذا لم نكن في Render، أو إذا طلبنا ذلك صراحة
DEBUG = env.bool('DJANGO_DEBUG', not IN_RENDER_DEPLOYMENT)

SECRET_KEY = env('DJANGO_SECRET_KEY')
DB_ENCRYPTION_KEY = env('DB_ENCRYPTION_KEY')

# السماح لجميع النطاقات (Render يدير الـ Routing، ومحلياً نحتاج localhost)
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
    'daphne', # يجب أن يكون في البداية
    
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
    "whitenoise.middleware.WhiteNoiseMiddleware", # أساسي لـ Render
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
    # --- إعدادات Render (Production) ---
    # يأخذ الإعدادات تلقائياً من DATABASE_URL الموجود في Render Dashboard
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=False)
    }
else:
    # --- إعدادات Local (Docker) ---
    # يأخذ الإعدادات من ملف .env المحلي
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='camp_medical_db'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST', default='db'), # اسم الخدمة في docker-compose
            'PORT': env('DB_PORT', default='5432'),
        }
    }

# ==============================================================================
# 🗄️ REDIS & CACHE
# ==============================================================================

# في Render نأخذه من متغيرات البيئة، محلياً نأخذه من .env
REDIS_URL = env('REDIS_URL', default='redis://redis:6379/0')

if REDIS_URL:
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

# ==============================================================================
# 📧 EMAIL SETTINGS (Gmail SMTP - Force IPv4 + SSL)
# ==============================================================================

USE_REAL_EMAIL = env.bool('USE_REAL_EMAIL', default=IN_RENDER_DEPLOYMENT)

if USE_REAL_EMAIL:
    # نستخدم نفس الباك إند المخصص الذي أنشأناه سابقاً (لحل مشكلة IPv6)
    EMAIL_BACKEND = 'apps.core.email_backend.IPv4EmailBackend'
    
    EMAIL_HOST = 'smtp.gmail.com'
    
    # 🛑 التغيير الجوهري هنا: نستخدم بورت SSL بدلاً من TLS
    EMAIL_PORT = 465
    EMAIL_USE_TLS = False  # نوقف TLS
    EMAIL_USE_SSL = True   # نشغل SSL (أكثر توافقاً مع السيرفرات)
    
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
    
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# 🧠 AI SERVICES (Azure)
# ==============================================================================
# هذه المفاتيح مطلوبة في البيئتين
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

# استراتيجية التخزين:
# في Render: نستخدم Azure Blob Storage (لأن التخزين المحلي يختفي).
# محلياً: نستخدم Local Storage (أسهل وأسرع)، إلا إذا أردت تجربة Azure.
if IN_RENDER_DEPLOYMENT:
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
    MEDIA_URL = f"https://{env('AZURE_STORAGE_ACCOUNT_NAME', default='')}.blob.core.windows.net/media/"
else:
    # Local
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

# Unfold Admin Theme
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
# 👮 CSP & Security
# ==============================================================================
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
        "https://*.onrender.com", 
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
            "ws://127.0.0.1:8000",
            "wss://*.onrender.com",
            "https://*.blob.core.windows.net",
            "https://*.openai.azure.com",
        ],
    }
}

if IN_RENDER_DEPLOYMENT:
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





# أضف هذا في نهاية settings.py للتشخيص
import logging
logger = logging.getLogger(__name__)

# تشخيص مسارات القوالب
for template_engine in TEMPLATES:
    for loader in template_engine.get('DIRS', []):
        logger.info(f"🔍 Template directory: {loader}")
        logger.info(f"📁 Exists: {os.path.exists(loader)}")