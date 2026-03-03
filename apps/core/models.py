# apps/core/models.py
from django.db import models

class SystemSetting(models.Model):
    retention_days = models.IntegerField(
        default=14, 
        verbose_name="Keep Data For (Days)",
        help_text="Messages older than this will be auto-deleted."
    )
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"

    def __str__(self):
        return f"System Settings (Retention: {self.retention_days} days)"

    # لضمان وجود صف واحد فقط للإعدادات (Singleton Pattern)
    def save(self, *args, **kwargs):
        if not self.pk and SystemSetting.objects.exists():
            return # منع إنشاء أكثر من إعداد
        return super().save(*args, **kwargs)