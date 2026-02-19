from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

# الحصول على مودل المستخدم الحالي بشكل آمن
# Get current User model safely
User = get_user_model()

class RefugeeRegistrationForm(forms.ModelForm):
    """
    نموذج تسجيل اللاجئين (للواجهة الأمامية)
    Refugee Registration Form (Frontend)
    """
    # حقول كلمة المرور (للتأكد من التطابق)
    # Password fields (to ensure match)
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    email = forms.EmailField(label="Email Address", required=True)
    
    # تخصيص حقل اسم المستخدم ليظهر كـ "رقم صحي"
    # Customize username field to appear as "Health Number"
    username = forms.CharField(
        label="Health Number",
        help_text="Must be digits only"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'native_language', 'full_name']

    def clean_username(self):
        """التحقق من أن الرقم الصحي يحتوي على أرقام فقط وغير مكرر / Validate that Health Number contains digits only and is unique"""
        username = self.cleaned_data.get('username')
        if not username.isdigit():
            raise ValidationError("Health Number must contain numbers only.")
        
        if User.objects.filter(username=username).exists():
             raise ValidationError("This Health Number is already registered.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean(self):
        """التحقق من تطابق كلمتي المرور / Validate password match"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        """حفظ المستخدم وتعيين الدور كلاجئ / Save user and set role as Refugee"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = "REFUGEE" # استخدام النص مباشرة أو User.Role.REFUGEE / Use text directly or User.Role.REFUGEE
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # نذكر فقط الحقول الحقيقية الموجودة في المودل
        # Mention only real fields in the model
        # لا تضع password_1 أو password_2 هنا
        # Do not put password_1 or password_2 here
        fields = ('username', 'full_name', 'role', 'native_language')