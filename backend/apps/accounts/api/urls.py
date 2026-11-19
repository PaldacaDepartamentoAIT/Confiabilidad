from django.urls import path

from apps.accounts.api.auth_views import (
    AppLoginView,
    AppLogoutView,
    AppSessionView,
    BrowserLoginView,
    BrowserLogoutView,
    BrowserSessionView,
)
from apps.accounts.api.flow_views import (
    AppCompleteView,
    AppOptionsView,
    AppResendView,
    AppStatusView,
    AppVerifyView,
    BrowserCompleteView,
    BrowserOptionsView,
    BrowserResendView,
    BrowserStatusView,
    BrowserVerifyView,
)
from apps.accounts.api.views import AppRegistrationView, BrowserRegistrationView

urlpatterns = [
    path(
        "browser/v1/registration",
        BrowserRegistrationView.as_view(),
        name="registration-browser",
    ),
    path("app/v1/registration", AppRegistrationView.as_view(), name="registration-app"),
    path(
        "browser/v1/registration/verify",
        BrowserVerifyView.as_view(),
        name="registration-verify-browser",
    ),
    path("app/v1/registration/verify", AppVerifyView.as_view(), name="registration-verify-app"),
    path(
        "browser/v1/registration/resend",
        BrowserResendView.as_view(),
        name="registration-resend-browser",
    ),
    path("app/v1/registration/resend", AppResendView.as_view(), name="registration-resend-app"),
    path(
        "browser/v1/registration/status",
        BrowserStatusView.as_view(),
        name="registration-status-browser",
    ),
    path("app/v1/registration/status", AppStatusView.as_view(), name="registration-status-app"),
    path(
        "browser/v1/registration/options",
        BrowserOptionsView.as_view(),
        name="registration-options-browser",
    ),
    path("app/v1/registration/options", AppOptionsView.as_view(), name="registration-options-app"),
    path(
        "browser/v1/registration/complete",
        BrowserCompleteView.as_view(),
        name="registration-complete-browser",
    ),
    path(
        "app/v1/registration/complete",
        AppCompleteView.as_view(),
        name="registration-complete-app",
    ),
    path("browser/v1/auth/login", BrowserLoginView.as_view(), name="auth-login-browser"),
    path("app/v1/auth/login", AppLoginView.as_view(), name="auth-login-app"),
    path("browser/v1/auth/session", BrowserSessionView.as_view(), name="auth-session-browser"),
    path("app/v1/auth/session", AppSessionView.as_view(), name="auth-session-app"),
    path("browser/v1/auth/logout", BrowserLogoutView.as_view(), name="auth-logout-browser"),
    path("app/v1/auth/logout", AppLogoutView.as_view(), name="auth-logout-app"),
]
