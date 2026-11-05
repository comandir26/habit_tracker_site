from django.urls import path

from .views import LoginView, LogoutView, MeView, ProfileView, RegisterView, TokenRefreshView


urlpatterns = [
    path("profile/", ProfileView.as_view(), name="auth-profile"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
