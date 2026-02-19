from django.urls import path # لاحظ استوردنا path بدلاً من re_path / Note: Imported path instead of re_path
from . import consumers

websocket_urlpatterns = [
    # استخدام محول uuid الجاهز من جانغو
    # Use Django's built-in UUID converter
    # هذا يغنيك عن كتابة Regex ويقبل الشرطات (-) تلقائياً
    # This saves you from writing Regex and accepts hyphens (-) automatically
    path('ws/chat/<uuid:session_id>/', consumers.ChatConsumer.as_asgi()),
]