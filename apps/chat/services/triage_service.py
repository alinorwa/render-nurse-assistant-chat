from apps.chat.models import DangerKeyword, ChatSession
import logging

logger = logging.getLogger(__name__)

class TriageService:
    @staticmethod
    def check_for_danger(text_content):
        """
        تفحص النص (سواء ترجمة أو تحليل AI) بحثاً عن كلمات خطرة.
        Checks text (both translation and AI analysis) for dangerous words.
        """
        if not text_content:
            return False

        # جلب الكلمات من الكاش أو القاعدة
        # Fetch words from cache or database
        danger_words = list(DangerKeyword.objects.filter(is_active=True).values_list('word', flat=True))
        
        # إضافة كلمات إنجليزية للطوارئ (احتياط لتحليل AI)
        # Add English emergency words (fallback for AI analysis)
        emergency_en = ["blood", "bleeding", "emergency", "urgent", "pain", "unconscious"]
        
        text_check = text_content.lower()
        
        # الفحص
        # Check
        if any(word in text_check for word in danger_words) or \
           any(word in text_check for word in emergency_en):
            return True
            
        return False

    @staticmethod
    def escalate_session(session_id):
        """تحويل الجلسة إلى طبيب (أحمر) / Escalate session to doctor (Red)"""
        if session_id:
            ChatSession.objects.filter(id=session_id).update(priority=2)
            logger.info(f"Session {session_id} escalated to DOCTOR.")

    @staticmethod
    def deescalate_session(session_id):
        """إعادة الجلسة لممرض (أخضر) / De-escalate session to nurse (Green)"""
        if session_id:
            ChatSession.objects.filter(id=session_id).update(priority=1)