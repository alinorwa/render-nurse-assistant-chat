from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from .models import SystemSetting
# نستورد الدالة مباشرة وليس كـ Task لنشغلها يدوياً ونأخذ النتيجة
from apps.chat.tasks import delete_old_data 

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('retention_days',)
    
    # تحديد القالب المخصص
    change_form_template = "admin/core/systemsetting/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # لاحظ أننا أزلنا الـ / من البداية لضمان عملها داخل الـ namespace الخاص بالـ admin
            path('run-cleanup/', self.admin_site.admin_view(self.run_cleanup_view), name='run_gdpr_cleanup'),
        ]
        return custom_urls + urls


    def run_cleanup_view(self, request):
        try:
            # 🛑 تشغيل التنظيف فوراً (بدون delay) للحصول على نتيجة
            # ملاحظة: هذا آمن لأن العملية سريعة، وإذا طالت قليلاً سينتظر المتصفح
            # بما أننا استدعينا الدالة مباشرة، ستعود القيم التي طبعناها في الـ return أو الـ Logs
            # لكن دالة Celery لا ترجع قيماً عادة، لذا سنعتمد على رسالة النجاح العامة
            
            # استدعاء الدالة مباشرة (كأنها دالة بايثون عادية)
            delete_old_data() 
            
            # إظهار رسالة نجاح واضحة
            self.message_user(request, "✅ Cleanup process completed successfully. Old data has been removed.", messages.SUCCESS)
            
        except Exception as e:
            self.message_user(request, f"❌ Error during cleanup: {e}", messages.ERROR)

        # العودة للصفحة السابقة
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '../'))