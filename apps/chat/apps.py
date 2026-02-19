from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'

    def ready(self):
        # استيراد الإشارات عند بدء التطبيق
        import apps.chat.signals