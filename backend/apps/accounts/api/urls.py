from django.urls import path

from apps.accounts.api.flow_views import (
    AppResendView,
    AppStatusView,
    AppVerifyView,
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
]
