from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.core.dashboard import MedicalDashboardView # استيراد الكلاس الجديد / Import new class

urlpatterns = [
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='/admin/'), name='admin_logout'),
     path('admin/login/', auth_views.LoginView.as_view(
        template_name='admin/login.html',  # هنا نحدد ملفنا المصمم / Here we specify our designed file
        extra_context={                    # نمرر العنوان ليظهر في الصفحة / Pass title to appear on page
            'site_title': 'Medical Support System',
            'site_header': 'Camp Administration',
        }
    ), name='admin_login'),
    path('admin/', admin.site.urls),
     path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="accounts/reset_password.html"), 
         name='password_reset'),

    # 2. رسالة "تم الإرسال"
    # 2. "Sent" message
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="accounts/reset_password_done.html"), 
         name='password_reset_done'),

    # 3. الرابط الذي يضغط عليه في الإيميل (يحتوي على uid و token)
    # 3. Link clicked in email (contains uid and token)
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="accounts/reset_password_confirm.html"), 
         name='password_reset_confirm'),

    # 4. رسالة "تم التغيير بنجاح"
    # 4. "Changed Successfully" message
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="accounts/reset_password_complete.html"), 
         name='password_reset_complete'),

     path('dashboard/', MedicalDashboardView.as_view(), name='custom_dashboard'),
    
    # الروابط الأساسية للموقع (ويب فقط)
    # Main site URLs (Web only)
    path('auth/', include('apps.accounts.urls')),
    path('chat/', include('apps.chat.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)