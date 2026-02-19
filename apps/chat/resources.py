from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from apps.accounts.models import User
from .models import ChatSession , Message

class ChatSessionResource(resources.ModelResource):
    """
    تحديد شكل البيانات عند التصدير (Excel/CSV)
    Define data format on export (Excel/CSV)
    """
    
    # تخصيص عمود اللاجئ: نريد عرض (الرقم الصحي) بدلاً من ID قاعدة البيانات
    # Customize Refugee Column: We want to show (Health ID) instead of Database ID
    refugee_id = fields.Field(
        column_name='Refugee Health ID',
        attribute='refugee',
        widget=ForeignKeyWidget(User, 'username')
    )
    
    # تخصيص عمود الممرض: نريد عرض الاسم الكامل
    # Customize Nurse Column: We want to show full name
    nurse_name = fields.Field(
        column_name='Nurse Name',
        attribute='nurse',
        widget=ForeignKeyWidget(User, 'full_name')
    )

    # تخصيص الحالة (Priority) لتظهر كنص (Doctor/Nurse) وليس رقم (1/2)
    # Customize Priority to appear as text (Doctor/Nurse) instead of number (1/2)
    priority_display = fields.Field(
        column_name='Priority Status',
        attribute='get_priority_display'
    )

    class Meta:
        model = ChatSession
        # تحديد الحقول التي نريد تصديرها وترتيبها
        # Define fields to export and their order
        fields = ('id', 'refugee_id', 'nurse_name', 'priority_display', 'start_time', 'is_active', 'last_activity')
        export_order = ('id', 'refugee_id', 'nurse_name', 'priority_display', 'is_active', 'start_time')


class SessionMessageResource(resources.ModelResource):
    """
    تجهيز تقرير الرسائل لجلسة محددة
    Prepare message report for specific session
    """
    sender = fields.Field(column_name='Sender', attribute='sender__full_name')
    role = fields.Field(column_name='Role', attribute='sender__role')
    original = fields.Field(column_name='Original Text', attribute='text_original')
    translated = fields.Field(column_name='Translated Text', attribute='text_translated')
    analysis = fields.Field(column_name='AI Analysis', attribute='ai_analysis')
    time = fields.Field(column_name='Time', attribute='timestamp')

    class Meta:
        model = Message
        fields = ('time', 'sender', 'role', 'original', 'translated', 'analysis')
        export_order = ('time', 'sender', 'role', 'original', 'translated', 'analysis')        