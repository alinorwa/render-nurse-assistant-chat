import uuid 
import hashlib
import logging
import nh3
import base64

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Now
from django.db import transaction 

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)
User = settings.AUTH_USER_MODEL

# ... (كود EncryptedTextField و DangerKeyword و ChatSession يبقى كما هو تماماً) ...
# ... (EncryptedTextField, DangerKeyword, ChatSession code remains exactly as is) ...
# (انسخ الكلاسات الأولى من ملفك السابق وضعها هنا)
# (Copy first classes from your previous file and place here)

class EncryptedTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        key = settings.DB_ENCRYPTION_KEY
        self.fernet = Fernet(key)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if not value: return value
        clean_value = nh3.clean(value, tags=set())
        encrypted_data = self.fernet.encrypt(clean_value.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    
    def from_db_value(self, value, expression, connection):
        if not value: return value
        try:
            decrypted_data = self.fernet.decrypt(value.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return f"[Encrypted Data - Error]"
        
    def to_python(self, value):
        return value

class DangerKeyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=100, unique=True, verbose_name="Det farlige ordet (norsk)")
    is_active = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        self.word = self.word.lower().strip()
        super().save(*args, **kwargs)
    def __str__(self):
        return self.word

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refugee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', limit_choices_to={'role': 'REFUGEE'})
    nurse = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='nurse_sessions', limit_choices_to={'is_staff': True})
    start_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    PRIORITY_CHOICES = [(1, 'Nurse (Normal)'), (2, 'Doctor (Urgent)')]
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1, verbose_name="Priority Level")
    class Meta: ordering = ['-priority', '-last_activity']
    def __str__(self): return f"Chat: {self.refugee.full_name} ({self.get_priority_display()})"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    
    text_original = EncryptedTextField(verbose_name=_("Original Text"), blank=True, null=True)
    language_code = models.CharField(max_length=10, blank=True)
    text_translated = EncryptedTextField(blank=True, null=True, verbose_name=_("Translated Text"))
    image = models.ImageField(upload_to='chat_images/%Y/%m/', blank=True, null=True, verbose_name="Medical Image")
    audio = models.FileField(upload_to='chat_audio/%Y/%m/', blank=True, null=True, verbose_name="Voice Note")
    ai_analysis = EncryptedTextField(blank=True, null=True, verbose_name="AI Medical Analysis")

    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False, verbose_name="Urgent / Doctor")

    class Meta:
        ordering = ['timestamp']

    def save(self, *args, **kwargs):
        # منطق "بيانات" فقط (تحديد اللغة الافتراضية)
        # "Data" logic only (Define default language)
        if self.sender_id and not self.language_code:
            self.language_code = self.sender.native_language

        # حفظ نقي (المنطق كله انتقل إلى signals.py)
        # Pure save (All logic moved to signals.py)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender.username}: Message"

    




class TranslationCache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_hash = models.CharField(max_length=64, db_index=True)
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    source_text = EncryptedTextField()
    translated_text = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('source_hash', 'source_language', 'target_language')
    @staticmethod
    def make_hash(text): return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()
    def __str__(self): return f"{self.source_language}->{self.target_language}"



# أضف هذا الكلاس في نهاية ملف models.py
# Add this class at the end of models.py

class EpidemicAlert(models.Model):
    """
    جدول إنذار الأوبئة: يسجل التنبيهات عند تجاوز الحالات للحد الأقصى
    Epidemic Alert Table: Records alerts when cases exceed limit
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symptom_category = models.CharField(max_length=100, verbose_name="Possible type of epidemic")
    case_count = models.IntegerField(verbose_name="Number of cases detected")
    time_window_hours = models.IntegerField(default=1, verbose_name="Within (hours)")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # حقل للممرض ليضغط عليه عندما يتخذ إجراء (مثل: تم عزل المرضى)
    # Field for nurse to click when action is taken (e.g., patients isolated)
    is_acknowledged = models.BooleanField(default=False, verbose_name="Reviewed/Processed")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"🚨 ALERT: {self.symptom_category} ({self.case_count} cases)"
    





class ImageAnalysisCache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # البصمة الفريدة
    # Unique Hash
    image_hash = models.CharField(max_length=64, db_index=True, unique=True)
    
    # نسخة من الصورة للمراجعة
    # Image copy for review
    cached_image = models.ImageField(upload_to='cache_snapshots/%Y/', blank=True, null=True, verbose_name="Snapshot")
    
    # التحليل (مشفر)
    # Analysis (Encrypted)
    analysis_result = EncryptedTextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image Hash: {self.image_hash[:10]}..."



class CannedResponse(models.Model):
    text = models.TextField(verbose_name="Message Content")
    
    def __str__(self):
        return self.text[:50] + '...'