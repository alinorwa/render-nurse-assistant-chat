from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.functions import Now
from .models import Message, ChatSession
from .tasks import process_message_ai
from .services.triage_service import TriageService

import os
from django.db.models.signals import post_delete



@receiver(post_save, sender=Message)
def message_post_save(sender, instance, created, **kwargs):
    """
    مراقب الحفظ: يوزع المهام ويحدث الجلسة
    Save Observer: Distributes tasks and updates session
    """
    
    # 1. تحديث وقت الجلسة (لترتيب المحادثات)
    # 1. Update session time (for conversation ordering)
    if instance.session_id:
        ChatSession.objects.filter(id=instance.session_id).update(last_activity=Now())

    # متغيرات لتحديد هوية المرسل
    # Variables to identify sender
    is_nurse = instance.sender.is_staff
    is_refugee = instance.sender.role == 'REFUGEE'

    # 2. منطق الممرض (De-escalation)
    # 2. Nurse Logic (De-escalation)
    if is_nurse:
        TriageService.deescalate_session(instance.session_id)
        # 🛑 التصحيح: حذفنا الـ return من هنا لنسمح بالترجمة بالأسفل
        # 🛑 Correction: Removed return from here to allow translation below

    # 3. شروط تشغيل المعالجة الخلفية (Celery)
    # 3. Conditions to run background processing (Celery)
    
    # الشرط أ: اللاجئ أرسل رسالة (تحتاج ترجمة أو تحليل صورة أو فرز طبي)
    # Condition A: Refugee sent message (needs translation, image analysis, or medical triage)
    refugee_needs_processing = (
        is_refugee and (
            (instance.text_original and not instance.text_translated) or
            (instance.image and not instance.ai_analysis)
        )
    )

    # الشرط ب: الممرض أرسل رسالة (تحتاج ترجمة فقط لتصل للاجئ بلغته)
    # Condition B: Nurse sent message (needs translation only to reach refugee in their language)
    nurse_needs_translation = (
        is_nurse and 
        instance.text_original and 
        not instance.text_translated
    )

    # 4. التنفيذ
    # 4. Execution
    if refugee_needs_processing or nurse_needs_translation:
        # نستخدم on_commit لضمان أن البيانات حُفظت قبل أن يبدأ الـ Worker
        # Use on_commit to ensure data is saved before Worker starts
        transaction.on_commit(lambda: process_message_ai.delay(str(instance.id))) 



@receiver(post_delete, sender=Message)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    حذف الملفات من Azure (أو Local) عند حذف سجل الرسالة من قاعدة البيانات.
    Deletes file from filesystem/Azure when corresponding `Message` object is deleted.
    """
    
    # 1. حذف الصورة إن وجدت
    if instance.image:
        try:
            # save=False ضروري لعدم محاولة تحديث الموديل المحذوف
            instance.image.delete(save=False) 
        except Exception as e:
            print(f"Error deleting image file: {e}")

    # 2. حذف الصوت إن وجد
    if instance.audio:
        try:
            instance.audio.delete(save=False)
        except Exception as e:
            print(f"Error deleting audio file: {e}")