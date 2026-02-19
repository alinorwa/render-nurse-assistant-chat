import requests
import logging
import uuid
import time
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. Cache Repository (مسؤول عن قاعدة البيانات فقط)
# 1. Cache Repository (Responsible for database only)
# ==============================================================================
class CacheRepository:
    def __init__(self):
        # نجلبه ديناميكياً لتجنب مشاكل الاستيراد الدائري
        # Import dynamically to avoid circular import issues
        self.model = apps.get_model('chat', 'TranslationCache')

    def get(self, text, src, dest):
        try:
            text_hash = self.model.make_hash(text)
            cached = self.model.objects.filter(
                source_hash=text_hash,
                source_language=src,
                target_language=dest
            ).first()
            if cached:
                logger.info("✅ Cache HIT")
                return cached.translated_text
        except Exception as e:
            logger.warning(f"⚠️ Cache read error: {e}")
        return None

    def save(self, text, translated_text, src, dest):
        try:
            text_hash = self.model.make_hash(text)
            self.model.objects.create(
                source_hash=text_hash,
                source_language=src,
                target_language=dest,
                source_text=text,
                translated_text=translated_text
            )
        except Exception as e:
            logger.error(f"❌ Cache write error: {e}")


# ==============================================================================
# 2. Azure Client (مسؤول عن الاتصال الخارجي فقط)
# 2. Azure Client (Responsible for external connection only)
# ==============================================================================
class AzureClient:
    def __init__(self):
        self.api_key = getattr(settings, 'AZURE_TRANSLATOR_KEY', None)
        self.endpoint = getattr(settings, 'AZURE_TRANSLATOR_ENDPOINT', '')
        self.region = getattr(settings, 'AZURE_TRANSLATOR_REGION', 'global')
        
        if self.endpoint and not self.endpoint.endswith('/translate'):
            self.endpoint = f"{self.endpoint.rstrip('/')}/translate"

    def fetch_translation(self, text, src, dest):
        if not self.api_key or not self.endpoint:
            raise ValueError("Azure Credentials Missing")

        params = {
            'api-version': '3.0',
            'from': src,
            'to': dest
        }
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'Ocp-Apim-Subscription-Region': self.region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        body = [{'text': text}]

        response = requests.post(self.endpoint, params=params, headers=headers, json=body, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['translations'][0]['text']
            return None
        
        # نرفع الخطأ لكي تتعامل معه سياسة إعادة المحاولة
        # Raise error to be handled by retry policy
        response.raise_for_status()


# ==============================================================================
# 3. Retry Policy (مسؤول عن منطق الصبر وإعادة المحاولة)
# 3. Retry Policy (Responsible for retry logic and patience)
# ==============================================================================
class RetryPolicy:
    def __init__(self, max_retries=3, delay_factor=2):
        self.max_retries = max_retries
        self.delay_factor = delay_factor

    def execute(self, func, *args, **kwargs):
        """
        ينفذ أي دالة ويمرر لها معاملاتها، ويعيد المحاولة عند الفشل
        Executes any function passing arguments, retries on failure
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            
            except requests.exceptions.HTTPError as e:
                # إذا كان الخطأ 429 (Too Many Requests) نعيد المحاولة
                # If error 429 (Too Many Requests), retry
                if e.response.status_code == 429:
                    wait_time = (attempt + 1) * self.delay_factor
                    logger.warning(f"⏳ Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    last_exception = e
                    continue
                # أخطاء أخرى (400, 500) لا نعيد المحاولة
                # Other errors (400, 500), do not retry
                logger.error(f"❌ HTTP Error: {e}")
                raise e

            except requests.exceptions.RequestException as e:
                # مشاكل في الشبكة
                # Network issues
                logger.warning(f"⚠️ Network error (Attempt {attempt+1}): {e}")
                time.sleep(1)
                last_exception = e
        
        # إذا استنفدنا المحاولات
        # If retries exhausted
        if last_exception:
            raise last_exception


# ==============================================================================
# 4. Azure Translator Service (المنسق / الواجهة الرئيسية)
# 4. Azure Translator Service (Coordinator / Main Interface)
# ==============================================================================
class AzureTranslator:
    def __init__(self):
        self.cache = CacheRepository()
        self.client = AzureClient()
        self.retry_policy = RetryPolicy()

    def translate(self, text, source_lang, target_lang):
        # 1. فحوصات سريعة
        # 1. Quick checks
        if not text: return ""
        if source_lang == target_lang: return text

        # 2. الكاش أولاً
        # 2. Cache first
        cached_result = self.cache.get(text, source_lang, target_lang)
        if cached_result:
            return cached_result

        # 3. الاتصال بـ Azure (عبر سياسة إعادة المحاولة)
        # 3. Connect to Azure (via retry policy)
        try:
            # نمرر دالة العميل إلى سياسة الإعادة
            # Pass client function to retry policy
            translated_text = self.retry_policy.execute(
                self.client.fetch_translation, 
                text, source_lang, target_lang
            )
            
            if translated_text:
                # 4. الحفظ في الكاش
                # 4. Save to cache
                self.cache.save(text, translated_text, source_lang, target_lang)
                return translated_text

        except Exception as e:
            # الفشل الآمن (Graceful Degradation)
            import traceback
            logger.error(f"💀 Translation failed completely: {e}")
            logger.error(traceback.format_exc())
            
            # في وضع الديباج، قد نرغب في رؤية الخطأ في الواجهة
            # In debug mode, we might want to see the error in UI
            if settings.DEBUG:
                 return f"[TR-ERROR] {text}"
            
            return text

        return text