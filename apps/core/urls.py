from django.urls import path
from .views import root_redirect_view, ServiceWorkerView, OfflineView

urlpatterns = [
    # الرابط الرئيسي يوجه للدالة الذكية
    # Main URL redirects to the smart function
    path('', root_redirect_view, name='home'),
    
    path('sw.js', ServiceWorkerView.as_view(), name='sw_js'),
    path('offline/', OfflineView.as_view(), name='offline'),
]