import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, make_user


def _history(user_id: int) -> list[str]:
    return list(
        User.history.filter(id=user_id)
        .order_by("history_date")
        .values_list("history_type", flat=True)
    )


HISTORY_METADATA = {
    "history_id",
    "history_date",
    "history_change_reason",
    "history_type",
    "history_user",
}


def test_history_tracks_every_field_except_password_and_last_login() -> None:
    tracked = {field.name for field in User.history.model._meta.concrete_fields}
    expected = {field.name for field in User._meta.concrete_fields} - {"password", "last_login"}

    assert tracked == expected | HISTORY_METADATA


@pytest.mark.django_db
def test_change_version_stores_the_new_data() -> None:
    user = make_user(name="Ana García", country="ES")
    user.name = "Ana López"
    user.country = "MX"
    user.is_staff = True
    user.save()

    version = User.history.get(id=user.pk, history_type="~")
    assert (version.email, version.name, version.country, version.is_staff) == (
        user.email,
        "Ana López",
        "MX",
        True,
    )
    assert version.history_date is not None


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
@pytest.mark.urls("apps.accounts.tests.history_urls")
def test_change_in_real_request_records_author(client: Client) -> None:
    admin = make_user()
    target = make_user()
    client.force_login(admin)

    resp = client.post(f"/rename/{target.pk}/", {"name": "Ana García"})

    assert resp.status_code == 204
    version = User.history.filter(id=target.pk).latest("history_date")
    assert (version.history_type, version.name, version.history_user) == ("~", "Ana García", admin)


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
