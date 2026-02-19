from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time

from .models import ChatSession, Message
from apps.core.services import AzureTranslator 

@login_required
def chat_room(request):
    user = request.user
    if user.is_staff:
        return redirect('admin:index')
    
    # رسالة الخصوصية
    # Privacy message
    base_warning = "🔒 For your privacy, do not write your name or health ID here. We identify you automatically."
    privacy_warning = base_warning 

    if user.native_language and user.native_language != 'en':
        try:
            translator = AzureTranslator()
            privacy_warning = translator.translate(base_warning, 'en', user.native_language)
        except:
            pass

    session, created = ChatSession.objects.get_or_create(refugee=user)
    
    return render(request, 'chat/room.html', {
        'session': session,
        'chat_messages': session.messages.all(),
        'privacy_warning': privacy_warning 
    })




@login_required
@require_POST
def upload_image(request): # يمكنك تسميتها upload_file ليكون الاسم أدق
    user = request.user
    session_id = request.POST.get('session_id')
    
    # استقبال إما صورة أو صوت
    image_file = request.FILES.get('image')
    audio_file = request.FILES.get('audio')

    if not session_id or (not image_file and not audio_file):
        return JsonResponse({'error': 'No file or session provided'}, status=400)

    try:
        session = ChatSession.objects.get(id=session_id)
        if session.refugee != user and session.nurse != user:
             return JsonResponse({'error': 'Unauthorized'}, status=403)

        # حفظ الرسالة
        with transaction.atomic():
            message = Message(session=session, sender=user)
            
            if image_file:
                message.image = image_file
                message.text_original = "[Image Sent]"
            
            if audio_file:
                message.audio = audio_file
                # نترك النص فارغاً ليقوم Whisper بتعبئته لاحقاً
                # أو نضع نصاً مؤقتاً
                if not message.text_original:
                    message.text_original = "🎤 ..." 

            message.save() # سيتم تفعيل Celery تلقائياً (كما برمجناه في models.py)

            # تجهيز رابط الملف للإشعار
            file_url = message.image.url if message.image else message.audio.url
            # نضيف Timestamp لكسر الكاش
            file_url = f"{file_url}?v={int(time.time())}"

            # إشعار الويب سوكيت
            def send_ws():
                channel_layer = get_channel_layer()
                
                payload = {
                    'type': 'chat_message',
                    'id': str(message.id),
                    'sender_id': user.id,
                    'text_original': message.text_original,
                    'text_translated': "",
                    'timestamp': message.timestamp.isoformat(),
                }
                
                if message.image:
                    payload['image_url'] = file_url
                if message.audio:
                    payload['audio_url'] = file_url # سنحتاج لمعالجة هذا في JS

                async_to_sync(channel_layer.group_send)(
                    f'chat_{session.id}',
                    payload
                )

            transaction.on_commit(send_ws)

        return JsonResponse({'status': 'success', 'url': file_url})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)