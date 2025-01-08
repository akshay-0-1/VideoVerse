# api/urls.py

from django.urls import path
from .views import RegistrationView, LoginView, ForgotPasswordView, ResetPasswordView, LogoutView
from . import views

urlpatterns = [
    path("register", RegistrationView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("forgotPassword", ForgotPasswordView.as_view(), name="forgotPassword"),
    path("resetPassword", ResetPasswordView.as_view(), name="resetPassword"),
    path('summaries/', views.video_summaries, name='video_summaries'),
    path('summaries/<int:pk>/', views.summary_details, name='summary_details'),
    path('generate-summary/', views.generate_summary, name='generate_summary'),
    path('verify-token', views.verify_token, name='verify_token'),
]