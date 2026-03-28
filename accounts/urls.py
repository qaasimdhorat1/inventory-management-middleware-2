"""
URL configuration for accounts app.
Provides endpoints for registration, JWT token management,
and user profile operations.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ChangePasswordView,
    PasswordResetView,
    RegisterView,
    UserProfileView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path(
        'change-password/',
        ChangePasswordView.as_view(),
        name='change-password',
    ),
    path(
        'reset-password/',
        PasswordResetView.as_view(),
        name='reset-password',
    ),
]