from django.urls import path

from apps.accounts.api.views import AppRegistrationView, BrowserRegistrationView

urlpatterns = [
    path(
        "browser/v1/registration",
        BrowserRegistrationView.as_view(),
        name="registration-browser",
    ),
    path("app/v1/registration", AppRegistrationView.as_view(), name="registration-app"),
]
