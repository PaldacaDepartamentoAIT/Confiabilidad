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
