"""
config/settings/base.py
Base settings shared across all environments.
"""

import os
from pathlib import Path
import environ
from datetime import timedelta
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# 1. تهيئة البيئة ومسار المشروع
env = environ.Env()

# 🛑 تعديل المسار: نصعد 3 خطوات للوصول للجذر (config -> settings -> base.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# قراءة .env من الجذر
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ==============================================================================
# 🧩 CORE APPS & MIDDLEWARE
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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
# 🌐 INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = 'Europe/Oslo'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 🐇 CELERY SHARED SETTINGS
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
# 🔒 AUTH & SECURITY (AXES)
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

# Axes Configuration
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=1)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_CLIENT_IP_CALLABLE = 'apps.core.utils.get_client_ip'
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
# 🛑 زيادة حد الحقول في النماذج (لحل مشكلة الجلسات الطويلة في الأدمن)
# القيمة الافتراضية 1000، سنرفعها إلى 10,000 لتتحمل محادثات طويلة جداً
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# ==============================================================================
# 🧠 AI SERVICES (Azure) - Shared
# ==============================================================================
AZURE_TRANSLATOR_KEY = env('AZURE_TRANSLATOR_KEY', default='')
AZURE_TRANSLATOR_ENDPOINT = env('AZURE_TRANSLATOR_ENDPOINT', default='')
AZURE_TRANSLATOR_REGION = env('AZURE_TRANSLATOR_REGION', default='')

AZURE_OPENAI_ENDPOINT = env('AZURE_OPENAI_ENDPOINT', default='')
AZURE_OPENAI_KEY = env('AZURE_OPENAI_KEY', default='')
AZURE_OPENAI_DEPLOYMENT_NAME = env('AZURE_OPENAI_DEPLOYMENT_NAME', default='gpt-4o')

# ==============================================================================
# 🎨 STATIC FILES
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

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

# ==============================================================================
# 👮 CSP & Security (Shared Rules)
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
        "img-src": ["'self'", "data:", "https://www.gravatar.com", "https://*.blob.core.windows.net", "https://campmedia2026.blob.core.windows.net"],
        "media-src": ["'self'", "data:", "https://*.blob.core.windows.net", "https://campmedia2026.blob.core.windows.net"],
        "connect-src": [
            "'self'",
            "ws://localhost:8000",
            "ws://127.0.0.1:8000",
            "wss://*.onrender.com",
            "https://*.blob.core.windows.net",
            "https://*.openai.azure.com"
        ],
    }
}




# Unfold Theme Settings


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
        "show_search": False,
        "show_all_applications": False,
        "navigation": [

            # ======================
            # Overview
            # ======================
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

            # ======================
            # Medical Operations
            # ======================
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
                    {
                        "title": _("Canned Responses"),
                        "icon": "quickreply",
                        "link": reverse_lazy("admin:chat_cannedresponse_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": _("Image Analysis Caches"),
                        "icon": "image",
                        "link": reverse_lazy("admin:chat_imageanalysiscache_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                    {
                        "title": _("Translation Caches"),
                        "icon": "translate",
                        "link": reverse_lazy("admin:chat_translationcache_changelist"),
                        "permission": lambda request: request.user.is_staff,
                    },
                ],
            },

            # ======================
            # Users & Staff
            # ======================
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

     "STYLES": [
      
        lambda request: static("css/admin_chat_clean.css"), # إذا كان لديك ملفات أخرى
    ],
    
}