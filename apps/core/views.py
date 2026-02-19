from django.shortcuts import redirect, render
from django.views.generic import TemplateView

def root_redirect_view(request):
    """
    هذه الدالة هي بوابة النظام الرئيسية (/)
    تقرر أين يذهب المستخدم بناءً على حالته.
    This function is the main system gateway (/)
    Decides where the user goes based on their status.
    """
    # 1. إذا لم يكن مسجلاً للدخول -> صفحة الدخول
    # 1. If not logged in -> Login page
    if not request.user.is_authenticated:
        return redirect('login')

    # 2. إذا كان ممرضاً (Admin/Staff) -> لوحة التحكم
    # 2. If nurse (Admin/Staff) -> Dashboard
    if request.user.is_staff:
        return redirect('admin:index')

    # 3. إذا كان لاجئاً -> صفحة الشات مباشرة
    # 3. If refugee -> Chat room directly
    return redirect('chat_room')

# (أبقِ على باقي الكلاسات مثل ServiceWorkerView كما هي)
# (Keep other classes like ServiceWorkerView as is)
class ServiceWorkerView(TemplateView):
    template_name = "sw.js"
    content_type = "application/javascript"

class OfflineView(TemplateView):
    template_name = "offline.html"