from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login ,logout
from django.shortcuts import redirect
from .forms import RefugeeRegistrationForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

class RefugeeRegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RefugeeRegistrationForm
    success_url = reverse_lazy('home') # التوجيه بعد النجاح / Redirect after success

    def form_valid(self, form):
        # 1. حفظ المستخدم في قاعدة البيانات
        # 1. Save user to database
        user = form.save()
        
        # 2. تسجيل الدخول مباشرة (Auto-Login)
        # 2. Auto-Login directly
        login(self.request, user , backend='django.contrib.auth.backends.ModelBackend')
        
        # 3. التوجيه للصفحة الرئيسية
        # 3. Redirect to home page
        return redirect(self.success_url)



class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # 1. التحقق من مربع "تذكرني"
        remember_me = self.request.POST.get('remember_me')
        
        if not remember_me:
            # إذا لم يضع صح: الجلسة تنتهي بمجرد إغلاق المتصفح
            self.request.session.set_expiry(0)
        else:
            # إذا وضع صح: الجلسة تستمر أسبوعين (أو حسب إعدادات SESSION_COOKIE_AGE)
            self.request.session.set_expiry(1209600) # 14 يوماً
            
        return super().form_valid(form) 


@login_required
@require_POST  # مهم جداً: الحذف يجب أن يكون POST وليس GET للأمان
def delete_account(request):
    user = request.user
    
    # التأكد من أن المستخدم ليس موظفاً (اختياري، لحماية النظام)
    if user.is_staff:
        messages.error(request, "Staff accounts cannot be deleted directly.")
        return redirect('chat:room')

    try:
        # 1. جلب الملفات المرتبطة لحذفها من Azure (اختياري ولكنه "نظيف")
        # Django Cascade سيحذف السجلات من قاعدة البيانات، 
        # لكن الملفات في Azure قد تبقى يتيمة (Orphaned) إلا إذا استخدمنا Signals أو حذفنا يدوياً.
        # سنعتمد هنا على Cascade للداتابيز، ويمكنك إضافة Signal لاحقاً للتنظيف العميق.
        
        # 2. تسجيل الخروج أولاً لتجنب مشاكل الجلسة
        logout(request)
        
        # 3. حذف المستخدم (سيحذف تلقائياً كل رسائله وجلساته بسبب on_delete=models.CASCADE)
        user.delete()
        
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('login') # أو صفحة تسجيل الدخول الرئيسية

    except Exception as e:
        # في حالة حدوث خطأ، نعيد المستخدم
        return redirect('chat:room')