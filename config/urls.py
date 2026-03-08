from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap

from apps.core.dashboard import MedicalDashboardView

# ==============================================================================
# 🌍 SEO Configuration (Sitemap & Robots)
# ==============================================================================

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        # ضع هنا أسماء الروابط (name='') للصفحات العامة التي تريد أرشفتها
        # تأكد أن هذه الأسماء موجودة فعلاً في urls.py
        return ['admin_login'] 

    def location(self, item):
        return reverse(item)

sitemaps = {
    'static': StaticViewSitemap,
}

# دالة robots.txt بسيطة
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /chat/",      # لا تؤرشف الشات (خصوصية)
        "Disallow: /admin/",     # لا تؤرشف لوحة التحكم
        "Disallow: /dashboard/", # لا تؤرشف الداشبورد
        "Allow: /",
        f"Sitemap: https://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

# ==============================================================================
# 🔗 URL Patterns
# ==============================================================================

urlpatterns = [
    # 1. SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt),

    # 2. Admin & Auth
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='/admin/'), name='admin_logout'),
    path('admin/login/', auth_views.LoginView.as_view(
        template_name='admin/login.html',
        extra_context={
            'site_title': 'Medical Support System',
            'site_header': 'Camp Administration',
        }
    ), name='admin_login'),
    
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    path('ali/', admin.site.urls),

    # 3. Password Reset URLs (إعادة تعيين كلمة المرور)
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="accounts/reset_password.html"), 
         name='password_reset'),

    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="accounts/reset_password_done.html"), 
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="accounts/reset_password_confirm.html"), 
         name='password_reset_confirm'),

    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="accounts/reset_password_complete.html"), 
         name='password_reset_complete'),

    # 4. Custom Dashboard
    path('dashboard/', MedicalDashboardView.as_view(), name='custom_dashboard'),
    
    # 5. Apps URLs
    path('auth/', include('apps.accounts.urls')),
    path('chat/', include('apps.chat.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)