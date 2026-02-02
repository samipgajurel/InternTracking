# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView, VerifyEmailView, LoginView, MeView,
    ForgotPasswordView, ResetPasswordView, ChangePasswordView,
    AdminCreateUserView, AdminAssignInternView, AdminUserListView
)

urlpatterns = [
    # auth
    path("signup/", SignupView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),

    # password flows
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),

    # admin user management
    path("admin/create-user/", AdminCreateUserView.as_view()),
    path("admin/assign-intern/", AdminAssignInternView.as_view()),
    path("admin/users/", AdminUserListView.as_view()),

    # refresh
    path("token/refresh/", TokenRefreshView.as_view()),
]
