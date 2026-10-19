from datetime import UTC, datetime

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from apps.accounts.models import User
from apps.audit.models import EventType, SecurityEvent

pytestmark = pytest.mark.django_db

CHANGELIST = "/admin/audit/securityevent/"
ADD = "/admin/audit/securityevent/add/"


@pytest.fixture
def viewer() -> User:
    user = User.objects.create_user(
        "auditor@x.com", "Clave-segura-2026!", name="Aud", birthdate="1990-01-01", country="ES"
    )
    user.is_staff = True
    user.save()
    user.user_permissions.add(Permission.objects.get(codename="view_securityevent"))
    return user


@pytest.fixture
def staff_without_permission() -> User:
    user = User.objects.create_user(
        "staff@x.com", "Clave-segura-2026!", name="Staff", birthdate="1990-01-01", country="ES"
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def event() -> SecurityEvent:
    return SecurityEvent.objects.create(event_type=EventType.LOGIN, success=True, ip="203.0.113.7")


def test_viewer_sees_events_in_changelist(viewer: User, event: SecurityEvent) -> None:
    client = Client()
    client.force_login(viewer)
    response = client.get(CHANGELIST)
    assert response.status_code == 200
    assert b"203.0.113.7" in response.content


def test_staff_without_permission_is_denied(staff_without_permission: User) -> None:
    client = Client()
    client.force_login(staff_without_permission)
    assert client.get(CHANGELIST).status_code == 403


def test_add_is_disabled_even_for_viewers(viewer: User) -> None:
    client = Client()
    client.force_login(viewer)
    assert client.get(ADD).status_code == 403


def test_change_and_delete_are_disabled(viewer: User, event: SecurityEvent) -> None:
    from django.contrib import admin

    model_admin = admin.site._registry[SecurityEvent]
    request = type("Req", (), {"user": viewer})()
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request, event) is False
    assert model_admin.has_delete_permission(request, event) is False


def test_change_permission_alone_does_not_grant_the_list(event: SecurityEvent) -> None:
    user = User.objects.create_user(
        "editor@x.com", "Clave-segura-2026!", name="Edi", birthdate="1990-01-01", country="ES"
    )
    user.is_staff = True
    user.save()
    user.user_permissions.add(Permission.objects.get(codename="change_securityevent"))
    client = Client()
    client.force_login(user)
    assert client.get(CHANGELIST).status_code == 403


def _event_at(created_at: "datetime", **fields: object) -> SecurityEvent:
    values = {"event_type": EventType.LOGIN, "success": True, "ip": "203.0.113.7"}
    values.update(fields)
    return SecurityEvent.objects.create(created_at=created_at, **values)


def _count(viewer: User, query: str) -> int:
    client = Client()
    client.force_login(viewer)
    response = client.get(CHANGELIST + query)
    assert response.status_code == 200
    return int(response.context["cl"].result_count)


def test_date_range_filter_keeps_only_events_inside_the_range(viewer: User) -> None:
    _event_at(datetime(2026, 1, 10, 12, tzinfo=UTC))
    _event_at(datetime(2026, 3, 5, 12, tzinfo=UTC))
    assert _count(viewer, "?desde=2026-03-01&hasta=2026-03-31") == 1


def test_type_and_result_filters(viewer: User) -> None:
    # force_login del cliente de prueba genera filas LOGIN; por eso se usan otros tipos.
    _event_at(datetime(2026, 3, 5, tzinfo=UTC), event_type=EventType.CODE_SENT, success=True)
    _event_at(datetime(2026, 3, 5, tzinfo=UTC), event_type=EventType.CODE_SENT, success=False)
    _event_at(datetime(2026, 3, 5, tzinfo=UTC), event_type=EventType.LOGOUT, success=True)
    assert _count(viewer, "?event_type__exact=code_sent") == 2
    assert _count(viewer, "?event_type__exact=code_sent&success__exact=0") == 1


def test_email_hash_search_is_exact(viewer: User) -> None:
    full = "a" * 64
    _event_at(datetime(2026, 3, 5, tzinfo=UTC), user_email_hash=full)
    assert _count(viewer, f"?q={full}") == 1
    assert _count(viewer, f"?q={full[:63]}") == 0


def test_ip_search_is_partial(viewer: User) -> None:
    _event_at(datetime(2026, 3, 5, tzinfo=UTC), ip="203.0.113.7")
    assert _count(viewer, "?q=203.0.113") == 1


def test_post_to_change_and_delete_cannot_modify_the_row(
    viewer: User, event: SecurityEvent
) -> None:
    client = Client()
    client.force_login(viewer)
    change = client.post(f"/admin/audit/securityevent/{event.pk}/change/", {"success": "on"})
    delete = client.post(f"/admin/audit/securityevent/{event.pk}/delete/", {"post": "yes"})
    assert change.status_code == 403
    assert delete.status_code == 403
    assert SecurityEvent.objects.filter(pk=event.pk).exists()
