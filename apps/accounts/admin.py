from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomUserCreationForm
from unfold.admin import ModelAdmin

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    add_form = CustomUserCreationForm
    model = User
    
    list_display = ('username', 'full_name', 'native_language_display', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'native_language', 'is_staff', 'is_active')
    search_fields = ('username', 'full_name')
    ordering = ('username',)
    
    list_filter_submit = True
    list_fullwidth = True
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        ('Identification', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'role', 'native_language')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # --- التعديل الجذري هنا ---
    # --- Radical modification here ---
    # حذفنا password_1 و password_2 من هنا
    # Removed password_1 and password_2 from here
    # لأن UserCreationForm سيجبر Django على عرضهما تلقائياً
    # Because UserCreationForm will force Django to display them automatically
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'full_name',
                'role',
                'native_language',
                # تم حذف password_1 و password_2 لتجنب الخطأ
                # password_1 and password_2 removed to avoid error
                'password1', # حقل الباسورد الأول / First password field
                'password2', # حقل تأكيد الباسورد / Password confirmation field
                
            ),
        }),
    )

    def native_language_display(self, obj):
        return f"{obj.get_native_language_display()}"
    native_language_display.short_description = 'Language'