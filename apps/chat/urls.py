from django.urls import path
from .views import chat_room, upload_image

urlpatterns = [
    path('', chat_room, name='chat_room'),
    path('upload/', upload_image, name='chat_upload_image'),
]