import os
import django

# يجب إعداد المتغيرات قبل استدعاء أي شيء يخص جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.chat.routing

application = ProtocolTypeRouter({
    # للطلبات العادية (HTTP)
    "http": get_asgi_application(),
    
    # لطلبات الـ WebSocket
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.chat.routing.websocket_urlpatterns
        )
    ),
})