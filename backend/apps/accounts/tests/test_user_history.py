import pytest
from django.http import HttpRequest, HttpResponse
from django.test import Client, RequestFactory
from django.utils import timezone
from simple_history.middleware import HistoryRequestMiddleware

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user


def _history(user_id: int) -> list[str]:
    return list(
        User.history.filter(id=user_id)
        .order_by("history_date")
        .values_list("history_type", flat=True)
    )


def test_history_excludes_password_and_last_login() -> None:
    fields = {field.name for field in User.history.model._meta.get_fields()}

    assert {"email", "name", "birthdate", "country", "is_active"} <= fields
    assert not {"password", "last_login"} & fields


@pytest.mark.django_db
def test_create_change_and_delete_are_recorded() -> None:
    user = make_user()
    user.name = "Ana García"
    user.save()
    user_id = user.pk
    user.delete()

    assert _history(user_id) == ["+", "~", "-"]


@pytest.mark.django_db
def test_history_survives_physical_deletion() -> None:
    user = make_user(name="Ana García")
    user_id = user.pk
    user.delete()

    assert not User.objects.filter(pk=user_id).exists()
    assert User.history.filter(id=user_id, name="Ana García").exists()


@pytest.mark.django_db
def test_console_change_has_no_author() -> None:
    user = make_user()

    assert User.history.get(id=user.pk).history_user is None


@pytest.mark.django_db
def test_change_in_authenticated_request_records_author(rf: RequestFactory) -> None:
    admin = make_user()
    target = make_user()
    request = rf.post("/")
    request.user = admin

    def view(_: HttpRequest) -> HttpResponse:
        target.name = "Ana García"
        target.save()
        return HttpResponse()

    HistoryRequestMiddleware(view)(request)

    assert User.history.filter(id=target.pk).latest("history_date").history_user == admin


@pytest.mark.django_db
def test_saving_only_excluded_fields_creates_no_version() -> None:
    user = make_user()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    assert _history(user.pk) == ["+"]


@pytest.mark.django_db
def test_login_creates_no_version() -> None:
    user = make_user(email="history-login@example.com")

    resp = Client().post(
        "/_allauth/app/v1/auth/login",
        data={"email": user.email, "password": DEFAULT_PASSWORD},
        content_type="application/json",
    )

    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.last_login is not None
    assert _history(user.pk) == ["+"]
