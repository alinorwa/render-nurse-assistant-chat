from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.html import mark_safe , format_html
from .models import ChatSession, Message, TranslationCache, DangerKeyword, EpidemicAlert, ImageAnalysisCache
from unfold.admin import ModelAdmin, TabularInline
from .services.notification_service import NotificationService
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm 
from .resources import ChatSessionResource , SessionMessageResource
from django.urls import path
from django.http import HttpResponse

# =========================================================
# 1. إعدادات الأوبئة
# =========================================================
@admin.action(description="✅ Mark as CONTROLLED")
def mark_as_controlled(modeladmin, request, queryset):
    queryset.update(is_acknowledged=True)
    modeladmin.message_user(request, "Selected alerts marked as controlled.")

    
@admin.register(EpidemicAlert)
class EpidemicAlertAdmin(ModelAdmin):
    list_display = ('status_badge', 'clean_category', 'case_count', 'timestamp')
    list_filter = ('is_acknowledged', 'symptom_category', 'timestamp')
    search_fields = ('symptom_category',) 
    readonly_fields = ('symptom_category', 'case_count', 'time_window_hours', 'timestamp')
    actions = [mark_as_controlled]
    ordering = ('-timestamp',)

      # --- دالة جديدة لتنظيف الاسم ---
    def clean_category(self, obj):
        # نأخذ النص، ونفصله عند القوس '('، ونأخذ الجزء الأول فقط
        return obj.symptom_category.split('(')[0].strip()
    
    clean_category.short_description = "Possible type of epidemic"
    clean_category.admin_order_field = 'symptom_category'

    def status_badge(self, obj):
        # حالة مسيطر عليها
        if obj.is_acknowledged:
            return format_html(
                '<div style="background-color: #10b981; color: white; padding: 5px 10px; border-radius: 6px; text-align: center; font-weight: bold; width: 140px;">{}</div>',
                '✅ CONTROLLED'
            )
        
        # حالة طارئة (حذفنا كود الستايل من هنا واستخدمنا الكلاس alert-pulse)
        return format_html(
            '<div class="alert-pulse" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 6px; text-align: center; font-weight: bold; width: 160px;">{}</div>',
            '🚨 ACTIVE OUTBREAK'
        )
    status_badge.short_description = "Status"

    # 🛑 إضافة مهمة جداً: ربط ملف CSS بهذا الكلاس أيضاً
    class Media:
        css = {
            'all': ('css/admin_chat_clean.css',) 
        }

# =========================================================
# 2. إعدادات الشات (تصحيح اختفاء الرسائل)
# =========================================================
class MessageInline(TabularInline):
    model = Message
    extra = 1
    tab = True
    
    fields = ('sender_display', 'smart_content_display', 'status_and_time', 'text_original', 'image')
    readonly_fields = ('sender_display', 'smart_content_display', 'status_and_time')
    

    def smart_content_display(self, obj):
        # 🛑 التصحيح: حذفنا النص الفارغ "" من القائمة
        IGNORED_TEXTS = [
            "[Image Sent]", "[Image from App]", "[bilde sendt]", 
            "[Image Sent from App]", "Sent a photo", "sendte et bilde"
        ]
        
        # 1. تجهيز النص المترجم (للاجئ)
        text_translated = None
        if obj.text_translated:
            clean_text = obj.text_translated.strip()
            # نعرض النص فقط إذا لم يكن في قائمة التجاهل
            if clean_text and clean_text not in IGNORED_TEXTS:
                text_translated = clean_text

        # 2. تجهيز النص الأصلي (للممرض)
        text_original = None
        if obj.text_original:
            clean_text = obj.text_original.strip()
            if clean_text and clean_text not in IGNORED_TEXTS:
                text_original = clean_text

        # استدعاء القالب (Template)
        return render_to_string('admin/chat/content.html', {
            'role': obj.sender.role if obj.sender_id else '',
            'text_original': text_original,
            'text_translated': text_translated,
            'image_url': obj.image.url if obj.image else None,
            'ai_analysis': obj.ai_analysis,
        })
    
    smart_content_display.short_description = "Content / Innhold"

    def status_and_time(self, obj):
        if not obj.pk: return "-"
        return render_to_string('admin/chat/status.html', {
            'is_urgent': obj.is_urgent,
            'time': obj.timestamp.strftime("%H:%M"),
            'date': obj.timestamp.strftime("%d %b %Y")
        })
    status_and_time.short_description = "Status"

    def sender_display(self, obj):
        if not obj.sender_id: return "-"
        color = "#3b82f6" if obj.sender.role == "NURSE" else "#10b981"
        role_name = "NURSE" if obj.sender.is_staff else "REFUGEE"
        return mark_safe(f'<div style="font-weight:bold; color:{color}">{role_name}<br><span class="text-gray-400 text-xs font-normal">{obj.sender.full_name}</span></div>')
    sender_display.short_description = "Sender"

    list_fullwidth = True
    
    class Media:
        css = {'all': ('css/admin_chat_clean.css',)}



# =========================================================
# 3. إعدادات جلسة المحادثة (التعديل الرئيسي هنا)
# =========================================================
@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = ChatSessionResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    # إضافة زر التصدير للقائمة الخارجية
    list_display = ('priority_badge', 'health_id', 'refugee_name', 'last_activity', 'export_action_button')
    list_filter = ('priority', 'is_active', 'start_time')
    inlines = [MessageInline]
    list_fullwidth = True
    
    search_fields = ('refugee__username', 'refugee__full_name')

    # إضافة زر التصدير (export_session_btn) إلى الحقول، وإخفاء الباقي
    fieldsets = (
        (None, {
            'fields': ('export_session_btn', 'refugee', 'nurse', 'priority'), 
            'classes': ('!hidden', 'hidden', 'd-none'),
        }),
    )
    
    # جعل الزر للقراءة فقط ليظهر
    readonly_fields = ('export_session_btn',)

    # --- دالة رسم زر التصدير داخل الجلسة ---
    def export_session_btn(self, obj):
        return mark_safe(
            '''
            <a href="export-chat/" class="bg-blue-600 text-white font-bold py-2 px-4 rounded inline-flex items-center hover:bg-blue-700 transition shadow-sm" target="_blank" style="text-decoration:none;">
                <span style="margin-right:8px; font-size:1.2em;">⬇️</span> 
                Export Chat History (Excel) 
            </a>
            '''
        )
    export_session_btn.short_description = "Reports"

    # --- دالة رسم زر التصدير في القائمة الخارجية ---
    def export_action_button(self, obj):
        return format_html(
            '<a href="{}/change/export-chat/" class="text-blue-600 hover:text-blue-800 font-bold" title="Download Excel">⬇️ Export</a>',
            obj.id
        )
    export_action_button.short_description = "Export"

    # --- الرابط المخصص ومنطق التصدير ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/change/export-chat/',
                self.admin_site.admin_view(self.export_chat_view),
                name='chat_session_export',
            ),
        ]
        return custom_urls + urls

    def export_chat_view(self, request, object_id):
        session = self.get_object(request, object_id)
        if not session:
            return HttpResponse("Session not found", status=404)

        # 1. جلب البيانات
        dataset = SessionMessageResource().export(
            queryset=Message.objects.filter(session=session).order_by('timestamp')
        )
        
        # 2. تصحيح الخطأ: استخدام دالة export('xlsx') بدلاً من .xlsx
        export_data = dataset.export('xlsx')
        
        # 3. إرجاع الملف
        response = HttpResponse(
            export_data, 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Chat_Record_{session.refugee.username}_{session.id}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # --- الحفاظ على priority_badge كما طلبت ---
    def priority_badge(self, obj):
        return render_to_string('admin/chat/status.html', {'is_urgent': obj.priority == 2})
    priority_badge.short_description = "Status"

    def health_id(self, obj): return obj.refugee.username
    def refugee_name(self, obj): return obj.refugee.full_name

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects: obj.delete()
        for instance in instances:
            if not getattr(instance, 'sender_id', None):
                instance.sender = request.user
            instance.save()
            NotificationService.broadcast_message_update(instance)
        formset.save_m2m()
    
    class Media:
        js = ('js/admin_realtime.js',)
# =========================================================
# 3. باقي المودلز
# =========================================================
@admin.register(DangerKeyword)
class DangerKeywordAdmin(ModelAdmin):
    list_display = ('word', 'is_active')
    search_fields = ('word',)
    help_text = "Add dangerous Norwegian words."



#  image analys cached admin 

@admin.register(ImageAnalysisCache)
class ImageAnalysisCacheAdmin(ModelAdmin):
    # 1. القائمة الرئيسية
    list_display = ('image_list_preview', 'analysis_preview', 'created_at')
    
    search_fields = ('analysis_result',) 
    list_filter = ('created_at',)
    
    # 2. التفاصيل (هنا التعديل الجذري)
    # نحدد بدقة ما نريد عرضه، ونستبعد image_hash و cached_image (حقل الرفع)
    fields = ('image_detail_preview', 'analysis_result', 'created_at')
    
    # نجعلها للقراءة فقط
    readonly_fields = ('image_detail_preview', 'analysis_result', 'created_at')
    
    ordering = ('-created_at',)

    # --- دالة عرض الصورة الصغيرة في القائمة ---
    def image_list_preview(self, obj):
        if obj.cached_image:
            return format_html(
                '''
                <div style="width: 50px; height: 50px; overflow: hidden; border-radius: 6px; border: 1px solid #e5e7eb;">
                    <img src="{}" style="width: 100%; height: 100%; object-fit: cover;" />
                </div>
                ''',
                obj.cached_image.url
            )
        return "-"
    image_list_preview.short_description = "Img"

    # --- دالة عرض الصورة الكبيرة في التفاصيل ---
    def image_detail_preview(self, obj):
        if obj.cached_image:
            return format_html(
                '''
                <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px; border: 1px dashed #d1d5db; display: inline-block;">
                    <a href="{url}" target="_blank" title="Click to view full size">
                        <img src="{url}" 
                             style="max-height: 400px; max-width: 100%; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" 
                        />
                    </a>
                    <div style="margin-top: 8px; text-align: center; color: #6b7280; font-size: 0.8rem;">
                       A preserved copy of the original image
                    </div>
                </div>
                ''',
                url=obj.cached_image.url
            )
        return "❌ No image saved"
    image_detail_preview.short_description = "Cached Snapshot"

    # --- دالة مقتطف التحليل ---
    def analysis_preview(self, obj):
        if not obj.analysis_result:
            return "-"
        return f"{obj.analysis_result[:80]}..."
    analysis_preview.short_description = "AI Result Snippet"
    



    

@admin.register(TranslationCache)
class TranslationCacheAdmin(ModelAdmin):
    list_display = ('source_text', 'translated_text', 'source_language', 'target_language')