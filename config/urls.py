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
        # نضع الروابط العامة فقط
        return ['login'] 

    def location(self, item):
        return reverse(item)

sitemaps = {
    'static': StaticViewSitemap,
}

def robots_txt(request):
    lines =[
        "User-agent: *",
        "Disallow: /chat/",      
        "Disallow: /admin/",     
        "Disallow: /ali/",       
        "Disallow: /dashboard/", 
        "Allow: /",
        f"Sitemap: https://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

# ==============================================================================
# 🔗 URL Patterns
# ==============================================================================

urlpatterns =[
    # 1. SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt),

    # 2. المصيدة (Honeypot) - لحماية النظام
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),

    # 🛑 3. لوحة التحكم الحقيقية (Unfold)
    # تم حذف مسارات admin/login اليدوية، Unfold سيتولى الدخول والخروج بأمان تام
    path('ali/', admin.site.urls),

    # 4. Password Reset URLs
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

    # 5. Custom Dashboard
    path('dashboard/', MedicalDashboardView.as_view(), name='custom_dashboard'),
    
    # 6. Apps URLs (دخول المرضى العادي)
    path('auth/', include('apps.accounts.urls')),
    path('chat/', include('apps.chat.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)