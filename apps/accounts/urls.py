from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RefugeeRegisterView, CustomLoginView, delete_account

urlpatterns = [
    path('register/', RefugeeRegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
     path('delete/', delete_account, name='delete_account'),
]