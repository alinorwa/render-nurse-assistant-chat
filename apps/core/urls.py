from django.urls import path
from .views import robots_txt, root_redirect_view, ServiceWorkerView, OfflineView

urlpatterns = [
    # الرابط الرئيسي يوجه للدالة الذكية
    # Main URL redirects to the smart function
    path('', root_redirect_view, name='home'),
    
    path('sw.js', ServiceWorkerView.as_view(), name='sw_js'),
    path('offline/', OfflineView.as_view(), name='offline'),
     path("robots.txt", robots_txt),
]