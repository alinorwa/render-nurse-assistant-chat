from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.shortcuts import redirect
from .forms import RefugeeRegistrationForm

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