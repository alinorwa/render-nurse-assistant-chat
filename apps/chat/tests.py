from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch  # أداة المحاكاة (Mocking) / Mocking tool
from .models import ChatSession, Message, DangerKeyword
from .tasks import process_message_ai  # نستورد المهمة لتشغيلها يدوياً / Import task to run manually

User = get_user_model()

class TriageSystemTest(TestCase):
    def setUp(self):
        """تجهيز البيانات قبل كل اختبار / Prepare data before each test"""
        # 1. إنشاء المستخدمين
        # 1. Create users
        self.refugee = User.objects.create_user(
            username="refugee_test", 
            password="123", 
            role="REFUGEE", 
            native_language="ar",
            full_name="Refugee User"
        )
        self.nurse = User.objects.create_user(
            username="nurse_test", 
            password="123", 
            role="NURSE", 
            is_staff=True,
            full_name="Nurse User"
        )
        
        # 2. إضافة كلمة خطرة للتجربة
        # 2. Add dangerous keyword for testing
        DangerKeyword.objects.create(word="blod", is_active=True)
        
        # 3. إنشاء جلسة
        # 3. Create session
        self.session = ChatSession.objects.create(refugee=self.refugee, nurse=self.nurse)

    # نستخدم @patch لمنع الاتصال الحقيقي بـ Azure أثناء الاختبار
    # Use @patch to prevent real connection to Azure during testing
    @patch('apps.core.services.AzureTranslator.translate') 
    def test_normal_message_flow(self, mock_translate):
        """
        اختبار 1: رسالة عادية لا تحتوي خطراً.
        النتيجة المتوقعة: تظل الأولوية 1 (Nurse).
        Test 1: Normal message containing no danger.
        Expected Result: Priority remains 1 (Nurse).
        """
        # إعداد رد المترجم الوهمي (نرويجي عادي)
        # Setup mock translator response (Normal Norwegian)
        mock_translate.return_value = "Hei, hvordan går det?" 

        # 1. اللاجئ يرسل رسالة
        # 1. Refugee sends message
        msg = Message.objects.create(
            session=self.session,
            sender=self.refugee,
            text_original="مرحبا"
        )

        # 2. محاكاة عمل Celery (نشغل المهمة يدوياً)
        # 2. Simulate Celery work (Run task manually)
        process_message_ai(str(msg.id))
        
        # 3. التحقق من النتائج
        # 3. Verify results
        self.session.refresh_from_db()
        self.assertEqual(self.session.priority, 1) # يجب أن تبقى عادية / Should remain normal

    @patch('apps.core.services.AzureTranslator.translate')
    def test_urgent_message_escalation(self, mock_translate):
        """
        اختبار 2: رسالة خطرة (تحتوي كلمة Blod).
        النتيجة المتوقعة: تتحول الأولوية إلى 2 (Doctor).
        Test 2: Dangerous message (contains word Blod).
        Expected Result: Priority changes to 2 (Doctor).
        """
        # إعداد رد المترجم الوهمي (يحتوي كلمة خطرة)
        # Setup mock translator response (contains dangerous word)
        mock_translate.return_value = "Jeg har mye blod" 

        # 1. اللاجئ يرسل رسالة خطرة
        # 1. Refugee sends dangerous message
        msg = Message.objects.create(
            session=self.session,
            sender=self.refugee,
            text_original="لدي دم كثير"
        )

        # 2. محاكاة عمل Celery
        # 2. Simulate Celery work
        process_message_ai(str(msg.id))
        
        # 3. التحقق
        # 3. Verify
        self.session.refresh_from_db()
        msg.refresh_from_db()
        
        self.assertTrue(msg.is_urgent) # الرسالة تم تمييزها كطارئة / Message marked as urgent
        self.assertEqual(self.session.priority, 2) # الجلسة تحولت لطبيب / Session changed to Doctor

    def test_nurse_reply_deescalation(self):
        """
        اختبار 3: رد الممرض.
        النتيجة المتوقعة: تعود الأولوية إلى 1 فوراً (بدون Celery).
        Test 3: Nurse reply.
        Expected Result: Priority returns to 1 immediately (without Celery).
        """
        # أولاً: نرفع حالة الجلسة يدوياً إلى طارئة
        # First: Manually raise session status to urgent
        self.session.priority = 2
        self.session.save()
        
        # ثانياً: الممرض يرد
        # Second: Nurse replies
        # (المنطق هنا موجود داخل models.py save() لذا لا نحتاج لمحاكاة Celery)
        # (Logic here is inside models.py save(), so no need to simulate Celery)
        Message.objects.create(
            session=self.session,
            sender=self.nurse,
            text_original="Det går bra"
        )
        
        # ثالثاً: التحقق
        # Third: Verify
        self.session.refresh_from_db()
        self.assertEqual(self.session.priority, 1) # يجب أن تعود خضراء / Should return green