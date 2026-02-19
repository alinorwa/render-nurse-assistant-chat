import base64
import logging
import hashlib
import os
from openai import AzureOpenAI
from django.conf import settings
from django.core.files.base import ContentFile # ضروري لحفظ نسخة الكاش / Necessary to save cache copy

logger = logging.getLogger(__name__)

class MedicalImageAnalyzer:
    def __init__(self):
        self.api_key = getattr(settings, 'AZURE_OPENAI_KEY', None)
        self.endpoint = getattr(settings, 'AZURE_OPENAI_ENDPOINT', None)
        
        if self.api_key and self.endpoint:
            self.client = AzureOpenAI(
                api_key=self.api_key,  
                api_version="2024-12-01-preview", 
                azure_endpoint=self.endpoint
            )
        else:
            self.client = None
            
        self.deployment_name = getattr(settings, 'AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

    def analyze(self, image_field):
        """
        يستقبل كائن الملف (File Object) بدلاً من المسار (Path)
        ليتوافق مع Azure Blob Storage.
        Receives the File Object instead of the Path
        to be compatible with Azure Blob Storage.
        """
        # استيراد المودل هنا لتجنب Circular Import
        # Import model here to avoid Circular Import
        from apps.chat.models import ImageAnalysisCache

        if not self.client:
            return "⚠️ AI Service Not Configured."

        try:
            # 1. قراءة بيانات الصورة في الذاكرة
            # 1. Read image data into memory
            # نفتح الملف للقراءة الثنائية
            # Open file for binary reading
            image_field.open('rb')
            image_data = image_field.read()
            
            # نتأكد من إغلاق الملف (أو تركه مفتوحاً حسب الحاجة، لكن القراءة تمت)
            # Ensure file is closed (or left open as needed, but reading is done)
            # لا نغلقه هنا لأن Django يديره، لكن البيانات أصبحت في image_data
            # We don't close it here because Django manages it, but data is now in image_data
            
            if not image_data:
                return "⚠️ Could not read image data."

            # 2. حساب البصمة (Hash) من البيانات مباشرة
            # 2. Calculate Hash from data directly
            sha256_hash = hashlib.sha256(image_data).hexdigest()

            # 3. البحث في الكاش (التوفير)
            # 3. Search in Cache (Optimization)
            cached_entry = ImageAnalysisCache.objects.filter(image_hash=sha256_hash).first()
            if cached_entry:
                logger.info(f"🚀 Image Analysis Cache HIT: {sha256_hash[:10]}")
                return cached_entry.analysis_result

            # 4. التجهيز للإرسال (Base64 Encoding)
            # 4. Prepare for sending (Base64 Encoding)
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # 5. إرسال الطلب لـ Azure OpenAI
            # 5. Send request to Azure OpenAI
            # تعديل: تخفيف القيود لتجنب (Jailbreak Detection)
            # Fix: Relax constraints to avoid (Jailbreak Detection)
            prompt = """
            Describe the medical symptoms visible in this image.
            Provide any observation in Norwegian using this format:
            - **Funn:** [Observations]
            - **Mulig årsak:** [Possible causes based on visual evidence]
            - **Anbefaling:** [General suggestion which must end with: Contact a doctor]
            
            Disclaimer: This is for informational purposes only.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    { "role": "system", "content": "You are a helpful assistant that describes images." },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                        ],
                    }
                ],
                max_tokens=400,
                timeout=25
            )
            
            result_text = response.choices[0].message.content

            # 6. حفظ النتيجة + نسخة من الصورة في الكاش
            # 6. Save result + image copy to cache
            try:
                # نستخدم ContentFile لحفظ البيانات الثنائية كملف جديد في الكاش
                # Use ContentFile to save binary data as a new file in cache
                file_name = os.path.basename(image_field.name)
                
                ImageAnalysisCache.objects.create(
                    image_hash=sha256_hash,
                    analysis_result=result_text,
                    cached_image=ContentFile(image_data, name=file_name)
                )
            except Exception as db_err:
                logger.error(f"Failed to save image cache: {db_err}")

            return result_text

        except Exception as e:
            logger.error(f"Image Analysis Failed: {e}")
            return f"⚠️ AI Analysis Failed: {str(e)}"