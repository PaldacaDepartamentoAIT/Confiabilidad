import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import make_user
from apps.core.models import MaintenanceAlert, MaintenanceTaskName, MaintenanceTaskStatus

pytestmark = pytest.mark.django_db


def test_authorized_staff_can_view_and_filter_maintenance_admin(client: Client) -> None:
    now = timezone.now()
    MaintenanceTaskStatus.objects.create(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        started_at=now,
        finished_at=now,
        status=MaintenanceTaskStatus.Status.FAILURE,
        error_summary="RuntimeError: fail",
    )
    open_alert = MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_SECURITY_EVENTS,
        error_summary="open failure detail",
    )
    resolved_alert = MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_EXPIRED_SESSIONS,
        error_summary="resolved failure detail",
        resolved_at=now,
    )

    staff = make_user(email="ops@ejemplo.com", is_staff=True)
    perms = Permission.objects.filter(
        content_type__app_label="core", codename__startswith="view_maintenance"
    )
    staff.user_permissions.add(*perms)
    client.force_login(staff)

    alerts_url = reverse("admin:core_maintenancealert_changelist")
    status_resp = client.get(reverse("admin:core_maintenancetaskstatus_changelist"))
    assert status_resp.status_code == 200
    assert b"RuntimeError: fail" in status_resp.content
    for state, present, absent in (
        ("open", open_alert.error_summary.encode(), resolved_alert.error_summary.encode()),
        ("resolved", resolved_alert.error_summary.encode(), open_alert.error_summary.encode()),
    ):
        resp = client.get(f"{alerts_url}?state={state}")
        assert resp.status_code == 200
        assert present in resp.content and absent not in resp.content


def test_maintenance_admin_denies_unauthorized_staff_and_writes(client: Client) -> None:
    plain_staff = make_user(email="plain@ejemplo.com", is_staff=True)
    client.force_login(plain_staff)
    assert client.get(reverse("admin:core_maintenancetaskstatus_changelist")).status_code == 403
    assert client.get(reverse("admin:core_maintenancealert_changelist")).status_code == 403

    superuser = make_user(email="root@ejemplo.com", is_staff=True, is_superuser=True)
    alert = MaintenanceAlert.objects.create(
        task_name=MaintenanceTaskName.PURGE_STALE_REGISTRATIONS,
        error_summary="err",
    )
    client.force_login(superuser)
    delete_url = reverse("admin:core_maintenancealert_delete", args=[alert.pk])
    assert client.post(reverse("admin:core_maintenancealert_add")).status_code == 403
    assert client.post(delete_url).status_code == 403
