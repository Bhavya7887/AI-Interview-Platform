from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("interviews/<uuid:public_id>/", views.interview_detail, name="interview_detail"),
    path("interviews/<uuid:public_id>/answer/", views.submit_answer, name="submit_answer"),
    path("interviews/<uuid:public_id>/report/", views.report, name="report"),
]
