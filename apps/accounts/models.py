from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, username,email=None, password=None, **extra_fields):
        """
        دالة الإنشاء الأساسية.
        Base creation function.
        username: سيكون الرقم الصحي للاجئ، أو المعرف الوظيفي للممرض.
        username: Will be the Health ID for refugee, or job ID for nurse.
        """
        if not username:
            raise ValueError(_('The Username/ID must be set'))
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(username=username,email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        إنشاء الممرض المسؤول (Admin).
        Create Admin Nurse.
        هنا: username يمكن أن يكون أي اسم أو معرف (نصي).
        Here: username can be any name or ID (text).
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'NURSE') # تحديد الدور تلقائياً / Auto-set role
        extra_fields.setdefault('native_language', 'no') # اللغة الافتراضية / Default language

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username,email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        NURSE = "NURSE", "Nurse"
        REFUGEE = "REFUGEE", "Refugee"

    LANGUAGE_CHOICES = [
          ('en', 'English'),
         ('uk', 'Ukrainian'),
        ('ar', 'Arabic'),
         ("es", "Spanish"),
         ("so", "Somali"),
        ("ti", "Tigrinya"),
        ("zh", "Chinese"),
        ("ru", "Russian"),
        ("ps", "Pashto"),
        ("am", "Amharic"),
        ('ps', 'Pashto'),
         ("ku", "Kurdish"),
        ("fa", "Farsi"),
        
        # النرويجية للممرضين
        # Norwegian for nurses
        ('no', 'Norwegian'),
    ]

    # الحقل الموحد (Primary Identifier)
    # Unified Field (Primary Identifier)
    # للاجئ: يخزن الرقم الصحي.
    # For Refugee: Stores Health ID.
    # للممرض: يخزن اسم الدخول.
    # For Nurse: Stores Login Username.
    username = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name=_("Health Number / Username"),
        help_text=_("Refugees: Health Number (Digits). Nurses: Username.")
    )

    full_name = models.CharField(max_length=150, verbose_name=_("Full Name"))
    email = models.EmailField(unique=True, verbose_name=_("Email Address"))
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.REFUGEE)
    
    native_language = models.CharField(
        max_length=5, 
        choices=LANGUAGE_CHOICES, 
        default='en',
        verbose_name=_("Native Language")
    )

    # Permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name'] # الحقول المطلوبة عند إنشاء Superuser / Required fields when creating Superuser

    def __str__(self):
        return f"{self.full_name} ({self.username})"

    @property
    def is_refugee(self):
        return self.role == self.Role.REFUGEE