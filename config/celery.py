import os
from celery import Celery

# ضبط متغيرات بيئة جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# قراءة الإعدادات من settings.py (يجب أن تبدأ بـ CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# اكتشاف المهام تلقائياً في التطبيقات (tasks.py)
app.autodiscover_tasks()