import os
import tempfile
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from openai import AzureOpenAI

from .models import Message, EpidemicAlert
from .services.image_service import ImageService
from .services.triage_service import TriageService
from .services.notification_service import NotificationService
from apps.core.services import AzureTranslator
from apps.core.vision_analysis import MedicalImageAnalyzer

logger = logging.getLogger(__name__)

# ==============================================================================
# 🎙️ Audio Transcription Task (New Addition)
# ==============================================================================

@shared_task
def transcribe_voice_note(message_id):
    """
    مهمة خلفية لتحويل الصوت إلى نص باستخدام Azure OpenAI (Whisper)
    """
    try:
        # 1. جلب الرسالة
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            logger.error(f"❌ Message {message_id} not found.")
            return

        if not message.audio:
            logger.warning(f"⚠️ Message {message_id} has no audio file.")
            return

        logger.info(f"🎙️ Transcribing audio for message {message_id}...")

        # 2. إعداد عميل Azure OpenAI
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-01",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )

        # 3. معالجة الملف (تحميله مؤقتاً لأن Azure API يحتاج ملفاً فعلياً)
        # نحصل على الامتداد (.webm, .wav, .mp3)
        file_ext = os.path.splitext(message.audio.name)[1] or '.webm'
        
        # نستخدم tempfile لإنشاء ملف مؤقت آمن يحذف تلقائياً
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            # نقرأ الملف من Azure Storage (أو Local) ونكتبه في الملف المؤقت
            with message.audio.open('rb') as f:
                temp_file.write(f.read())
            temp_file_path = temp_file.name

        try:
            # 4. الإرسال إلى Azure Whisper
            with open(temp_file_path, "rb") as audio_file:
                # 🛑 تأكد أن اسم الـ Deployment في Azure هو "whisper"
                result = client.audio.transcriptions.create(
                    model="whisper", 
                    file=audio_file,
                )
            
            transcribed_text = result.text
            logger.info(f"✅ Transcription result: {transcribed_text}")

            # 5. تحديث الرسالة
            message.text_original = transcribed_text
            message.save()

            # 6. إرسال التحديث للشات (Real-time update)
            # لتحديث النص "Processing..." إلى النص الحقيقي
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{message.session.id}',
                {
                    'type': 'chat_message',
                    'id': str(message.id),
                    'sender_id': message.sender.id,
                    'text_original': message.text_original, # النص الجديد
                    'text_translated': message.text_translated,
                    'timestamp': message.timestamp.isoformat(),
                    'is_read': message.is_read,
                    'audio_url': message.audio.url, 
                }
            )
            
            # 🛑 بعد تحويل الصوت لنص، نرسل الرسالة لمهمة المعالجة (ترجمة + تحليل خطر)
            # لكي يتم ترجمة النص الصوتي أيضاً
            process_message_ai.delay(message.id)

        finally:
            # تنظيف: حذف الملف المؤقت
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        logger.error(f"❌ Error transcribing audio: {e}")

# ==============================================================================
# 🤖 Existing AI Processing Task
# ==============================================================================

@shared_task
def process_message_ai(message_id):
    try:
        # جلب الرسالة مع البيانات المرتبطة
        message = Message.objects.select_related('session', 'sender', 'session__refugee').get(id=message_id)
        fields_to_update = []
        is_urgent_detected = False

        # 1. ضغط الصورة
        if message.image:
            compressed = ImageService.compress_image(message.image)
            if compressed:
                filename = os.path.basename(message.image.name)
                filename = os.path.splitext(filename)[0] + '.jpg'
                message.image.save(filename, compressed, save=False)
                fields_to_update.append('image')

        # 2. الترجمة (للصوت المفرغ أو النص العادي)
        if message.text_original and not message.text_translated:
            translator = AzureTranslator()
            
            if message.sender.role == 'REFUGEE':
                target_lang = 'no'
            else:
                target_lang = message.session.refugee.native_language

            translation = translator.translate(
                message.text_original, 
                message.language_code or 'en', 
                target_lang
            )
            
            message.text_translated = translation
            fields_to_update.append('text_translated')

            if message.sender.role == 'REFUGEE':
                if TriageService.check_for_danger(translation):
                    is_urgent_detected = True

        # 3. تحليل الصورة
        if message.image and not message.ai_analysis:
            analyzer = MedicalImageAnalyzer()
            analysis = analyzer.analyze(message.image)
            message.ai_analysis = analysis
            fields_to_update.append('ai_analysis')

            if TriageService.check_for_danger(analysis):
                is_urgent_detected = True

        # 4. تطبيق التحديثات
        if is_urgent_detected:
            message.is_urgent = True
            fields_to_update.append('is_urgent')
            TriageService.escalate_session(message.session_id)

        # 5. الحفظ والإشعار
        if fields_to_update:
            message.save(update_fields=fields_to_update)
            NotificationService.broadcast_message_update(message)
            logger.info(f"Message {message_id} processed successfully.")

    except Message.DoesNotExist:
        logger.error(f"Message {message_id} not found.")
    except Exception as e:
        logger.error(f"Task processing error: {e}")

# ==============================================================================
# 🦠 Epidemic Early Warning Task
# ==============================================================================

@shared_task
def check_epidemic_outbreak():
    time_threshold = timezone.now() - timedelta(hours=1)
    
    epidemic_signatures = {
        "Gastrointestinal ": ["diaré", "oppkast", "kvalme", "magesmerter"],
        "Respiratory ": ["høy feber", "hoste", "tungpustet", "influensa"],
        "Skin ": ["skabb", "utslett", "intens kløe"],
    }

    DANGER_THRESHOLD = 5

    recent_messages = Message.objects.filter(
        timestamp__gte=time_threshold,
        sender__role='REFUGEE'
    ).select_related('session')

    detected_cases = {k: set() for k in epidemic_signatures.keys()}

    for msg in recent_messages:
        text_content = (msg.text_translated or "") + " " + (msg.ai_analysis or "")
        text_content = text_content.lower()
        
        for category, keywords in epidemic_signatures.items():
            for word in keywords:
                if word in text_content:
                    detected_cases[category].add(msg.session.refugee.id)
                    break 

    for category, affected_users in detected_cases.items():
        count = len(affected_users)
        
        if count >= DANGER_THRESHOLD:
            recent_alert = EpidemicAlert.objects.filter(
                symptom_category=category,
                timestamp__gte=time_threshold
            ).exists()

            if not recent_alert:
                EpidemicAlert.objects.create(
                    symptom_category=category,
                    case_count=count
                )
                logger.critical(f"🚨 EPIDEMIC DETECTED: {category} ({count} cases)")        

# ==============================================================================
# 🧹 GDPR Cleanup Task
# ==============================================================================

@shared_task
def delete_old_data():
    cutoff_date = timezone.now() - timedelta(days=14) # تم تصحيحها لـ 14 يوماً كما هو مطلوب
    
    old_messages = Message.objects.filter(timestamp__lt=cutoff_date)
    
    count = 0
    for msg in old_messages:
        if msg.image:
            try:
                msg.image.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting image file for msg {msg.id}: {e}")
        
        if msg.audio: # إضافة حذف ملفات الصوت أيضاً
            try:
                msg.audio.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting audio file for msg {msg.id}: {e}")

        msg.delete()
        count += 1

    if count > 0:
        logger.info(f"🧹 GDPR Cleanup: Deleted {count} old messages.")