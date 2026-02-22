from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
import traceback

from .models import ChatSession, Message
from apps.core.services import AzureTranslator 
# 🛑 استيراد المهام
from .tasks import transcribe_voice_note, process_message_ai

@login_required
def chat_room(request):
    user = request.user
    if user.is_staff:
        return redirect('admin:index')
    
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
def upload_image(request):
    user = request.user
    session_id = request.POST.get('session_id')
    
    image_file = request.FILES.get('image')
    audio_file = request.FILES.get('audio')

    if not session_id or (not image_file and not audio_file):
        return JsonResponse({'error': 'No file or session provided'}, status=400)

    try:
        session = ChatSession.objects.get(id=session_id)
        if session.refugee != user and session.nurse != user:
             return JsonResponse({'error': 'Unauthorized'}, status=403)

        with transaction.atomic():
            message = Message(session=session, sender=user)
            
            # معالجة الصورة
            if image_file:
                message.image = image_file
                message.text_original = "[Image Sent]"
            
            # معالجة الصوت
            if audio_file:
                message.audio = audio_file
                # نص مؤقت حتى ينتهي التحليل
                if not message.text_original:
                    message.text_original = "🎤 Processing audio..." 

            message.save() 

            # تجهيز الرابط
            file_url = ""
            if message.image:
                file_url = f"{message.image.url}?v={int(time.time())}"
            elif message.audio:
                file_url = f"{message.audio.url}?v={int(time.time())}"

            # إشعار الويب سوكيت الفوري
            def send_ws():
                try:
                    channel_layer = get_channel_layer()
                    
                    payload = {
                        'type': 'chat_message',
                        'id': str(message.id),
                        'sender_id': user.id,
                        'text_original': message.text_original,
                        'text_translated': "",
                        'timestamp': message.timestamp.isoformat(),
                        'is_read': False, 
                    }
                    
                    if message.image:
                        payload['image_url'] = file_url
                    if message.audio:
                        payload['audio_url'] = file_url

                    async_to_sync(channel_layer.group_send)(
                        f'chat_{session.id}',
                        payload
                    )
                except Exception as ws_error:
                    print(f"⚠️ WebSocket Send Failed: {ws_error}")
                    traceback.print_exc()

            transaction.on_commit(send_ws)

            # 🛑 تشغيل المهام الخلفية
            if audio_file:
                # إذا كان صوتاً، نحوله لنص أولاً (ثم هو سيستدعي الترجمة لاحقاً)
                transaction.on_commit(lambda: transcribe_voice_note.delay(message.id))
            elif image_file:
                # إذا كانت صورة، نعالجها مباشرة
                transaction.on_commit(lambda: process_message_ai.delay(message.id))

        return JsonResponse({'status': 'success', 'url': file_url})

    except Exception as e:
        print(f"❌ Upload View Error: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)