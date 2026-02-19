from celery import shared_task
from .models import Message
# استيراد الخدمات
# Import services
from apps.core.services import AzureTranslator
from apps.core.vision_analysis import MedicalImageAnalyzer
from .services.image_service import ImageService
from .services.triage_service import TriageService
from .services.notification_service import NotificationService
import logging


from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task
def process_message_ai(message_id):
    try:
        # جلب الرسالة مع البيانات المرتبطة (لتسريع الاستعلام)
        # Fetch message with related data (for query optimization)
        message = Message.objects.select_related('session', 'sender', 'session__refugee').get(id=message_id)
        fields_to_update = []
        is_urgent_detected = False

        # 1. ضغط الصورة (على القرص)
        # 1. Compress image (on disk)
        if message.image:
            compressed = ImageService.compress_image(message.image)
            if compressed:
                # حفظ الصورة المضغوطة مكان القديمة
                # Save compressed image replacing the old one
                # نستخدم save=False لأننا سنحفظ لاحقاً
                # Use save=False because we will save later
                import os
                filename = os.path.basename(message.image.name)
                # التأكد من الامتداد jpg
                # Ensure extension is jpg
                filename = os.path.splitext(filename)[0] + '.jpg'
                message.image.save(filename, compressed, save=False)
                fields_to_update.append('image')

        # 2. الترجمة (التعديل هنا: السماح بالترجمة للطرفين)
        # 2. Translation (Modification here: Allow translation for both sides)
        if message.text_original and not message.text_translated:
            translator = AzureTranslator()
            
            # تحديد اللغة الهدف بذكاء:
            # Smartly determine target language:
            # - إذا المرسل لاجئ -> نترجم للنرويجية (no)
            # - If sender is refugee -> translate to Norwegian (no)
            # - إذا المرسل ممرض -> نترجم للغة اللاجئ (native_language)
            # - If sender is nurse -> translate to refugee's language (native_language)
            if message.sender.role == 'REFUGEE':
                target_lang = 'no'
            else:
                target_lang = message.session.refugee.native_language

            # الترجمة
            # Translation
            translation = translator.translate(
                message.text_original, 
                message.language_code or 'en', 
                target_lang
            )
            
            message.text_translated = translation
            fields_to_update.append('text_translated')

            # فحص الخطر في الترجمة (فقط إذا كان المرسل لاجئاً)
            # Check danger in translation (Only if sender is refugee)
            # الممرض لا يحتاج لفحص كلامه بحثاً عن الخطر
            # Nurse doesn't need to check their speech for danger
            if message.sender.role == 'REFUGEE':
                if TriageService.check_for_danger(translation):
                    is_urgent_detected = True

        # 3. تحليل الصورة (AI Vision) - للاجئ فقط
        # 3. Image Analysis (AI Vision) - Refugee Only
        if message.image and not message.ai_analysis:
            analyzer = MedicalImageAnalyzer()
            analysis = analyzer.analyze(message.image)
            message.ai_analysis = analysis
            fields_to_update.append('ai_analysis')

            # فحص الخطر في التحليل
            # Check danger in analysis
            if TriageService.check_for_danger(analysis):
                is_urgent_detected = True

        # 4. تطبيق التحديثات (للأولوية)
        # 4. Apply updates (for priority)
        if is_urgent_detected:
            message.is_urgent = True
            fields_to_update.append('is_urgent')
            TriageService.escalate_session(message.session_id)

        # 5. الحفظ والإشعار
        # 5. Save and Notify
        if fields_to_update:
            message.save(update_fields=fields_to_update)
            # إرسال التحديث للجميع (ليظهر النص المترجم في الشات)
            # Broadcast update to all (to show translated text in chat)
            NotificationService.broadcast_message_update(message)
            logger.info(f"Message {message_id} processed successfully.")

    except Message.DoesNotExist:
        logger.error(f"Message {message_id} not found.")
    except Exception as e:
        logger.error(f"Task processing error: {e}")




# ... (الكود السابق في الملف process_message_ai ... اترك كل شيء فوق كما هو)

# ==============================================================================
# 🦠 Epidemic Early Warning Task (الإضافة الجديدة)
# 🦠 Epidemic Early Warning Task (New Addition)
# ==============================================================================

@shared_task
def check_epidemic_outbreak():
    from django.utils import timezone
    from datetime import timedelta
    from .models import EpidemicAlert, Message
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    # 1. تحديد النطاق الزمني (آخر ساعة)
    # 1. Define time window (last hour)
    time_threshold = timezone.now() - timedelta(hours=1)
    
    # القاموس الطبي
    # Medical Dictionary
    epidemic_signatures = {
        "Gastrointestinal ": ["diaré", "oppkast", "kvalme", "magesmerter"],
        "Respiratory ": ["høy feber", "hoste", "tungpustet", "influensa"],
        "Skin ": ["skabb", "utslett", "intens kløe"],
    }

    # حد الخطر (عدد الأشخاص)
    # Danger Threshold (Number of people)
    DANGER_THRESHOLD = 5

    # 2. جلب الرسائل (يجب جلبها لفك تشفيرها في الذاكرة)
    # 2. Fetch messages (must fetch to decrypt in memory)
    recent_messages = Message.objects.filter(
        timestamp__gte=time_threshold,
        sender__role='REFUGEE'
    ).select_related('session')

    # 3. الفحص اليدوي (لأن النصوص مشفرة)
    # 3. Manual check (because texts are encrypted)
    detected_cases = {k: set() for k in epidemic_signatures.keys()}

    for msg in recent_messages:
        # دمج النص المترجم وتحليل الذكاء الاصطناعي للبحث
        # Merge translated text and AI analysis for search
        text_content = (msg.text_translated or "") + " " + (msg.ai_analysis or "")
        text_content = text_content.lower()
        
        for category, keywords in epidemic_signatures.items():
            for word in keywords:
                if word in text_content:
                    detected_cases[category].add(msg.session.refugee.id)
                    break 

    # 4. تسجيل التنبيهات
    # 4. Record alerts
    for category, affected_users in detected_cases.items():
        count = len(affected_users)
        
        if count >= DANGER_THRESHOLD:
            # نتأكد من عدم تكرار التنبيه لنفس الفئة في نفس الساعة
            # Ensure no duplicate alert for same category in same hour
            recent_alert = EpidemicAlert.objects.filter(
                symptom_category=category,
                timestamp__gte=time_threshold
            ).exists()

            if not recent_alert:
                EpidemicAlert.objects.create(
                    symptom_category=category,
                    case_count=count
                )
                
                # إشعار للأدمن (اختياري عبر الويب سوكيت)
                # Notify Admin (Optional via WebSocket)
                logger.critical(f"🚨 EPIDEMIC DETECTED: {category} ({count} cases)")        






# ... حذف data كل 14 يوم ...
# ... Delete data every 14 days ...
import os

@shared_task
def delete_old_data():
    """
    مهمة تنظيف البيانات (GDPR & Storage):
    تحذف أي رسالة مر عليها 14 يوماً (أسبوعين).
    Data Cleanup Task (GDPR & Storage):
    Deletes any message older than 14 days (two weeks).
    """
    
    
    # 1. تحديد التاريخ (قبل 14 يوماً من الآن)
    # 1. Define date (14 days ago from now)
    cutoff_date = timezone.now() - timedelta(minutes=5)
    
    # 2. جلب الرسائل القديمة
    # 2. Fetch old messages
    old_messages = Message.objects.filter(timestamp__lt=cutoff_date)
    
    count = 0
    for msg in old_messages:
        # إذا كانت هناك صورة، نحذف الملف من الهارد ديسك أولاً
        # إذا كانت هناك صورة، نحذف الملف من التخزين (سواء محلي أو Azure)
        # If there is an image, delete file from storage (Local or Azure)
        if msg.image:
            try:
                msg.image.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting image file for msg {msg.id}: {e}")
        
        # حذف الرسالة من قاعدة البيانات
        # Delete message from database
        msg.delete()
        count += 1

    if count > 0:
        logger.info(f"🧹 GDPR Cleanup: Deleted {count} old messages/images.")
