import sys
import os
from io import BytesIO
from PIL import Image as PilImage
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging

logger = logging.getLogger(__name__)

class ImageService:
    @staticmethod
    def compress_image(image_field):
        """
        تقوم بضغط الصورة المرفقة وتعيد ملفاً جديداً (ContentFile).
        Compresses the attached image and returns a new file (ContentFile).
        """
        if not image_field:
            return None

        try:
            # فتح الصورة من التخزين (سواء محلي أو Azure)
            # Open image from storage (Local or Azure)
            image_field.open()
            im = PilImage.open(image_field)

            # تحويل الألوان
            # Convert colors
            if im.mode in ('RGBA', 'P'):
                im = im.convert('RGB')

            # التصغير
            # Resize
            im.thumbnail((1024, 1024), PilImage.Resampling.LANCZOS)

            # الحفظ في الذاكرة
            # Save to memory
            output = BytesIO()
            im.save(output, format='JPEG', quality=70, optimize=True)
            output.seek(0)
            
            # استيراد هنا لتجنب Circular Import
            # Import here to avoid Circular Import
            from django.core.files.base import ContentFile
            return ContentFile(output.read())

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return None