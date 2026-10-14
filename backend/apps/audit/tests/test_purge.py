from datetime import UTC, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.audit.models import EventType, SecurityEvent, purge_expired

pytestmark = pytest.mark.django_db


def _event(age: timedelta) -> SecurityEvent:
    return SecurityEvent.objects.create(
        event_type=EventType.LOGIN, success=True, created_at=timezone.now() - age
    )


def test_dry_run_reports_old_events_without_deleting() -> None:
    old = _event(timedelta(days=400))
    recent = _event(timedelta(days=10))
    out = StringIO()
    call_command("purge_security_events", "--dry-run", stdout=out)
    assert "1 security events would be deleted" in out.getvalue()
    assert SecurityEvent.objects.filter(pk__in=[old.pk, recent.pk]).count() == 2


def test_purge_deletes_only_events_older_than_one_year() -> None:
    old = _event(timedelta(days=400))
    borderline_recent = _event(timedelta(days=364))
    out = StringIO()
    call_command("purge_security_events", stdout=out)
    assert "1 security events deleted" in out.getvalue()
    assert not SecurityEvent.objects.filter(pk=old.pk).exists()
    assert SecurityEvent.objects.filter(pk=borderline_recent.pk).exists()


def test_purge_with_nothing_to_delete_deletes_nothing() -> None:
    recent = _event(timedelta(days=1))
    call_command("purge_security_events", stdout=StringIO())
    assert SecurityEvent.objects.filter(pk=recent.pk).exists()


def test_retention_cutoff_is_one_calendar_year_across_leap_day() -> None:
    from datetime import datetime

    from apps.audit.models import retention_cutoff

    assert retention_cutoff(datetime(2028, 3, 1, tzinfo=UTC)) == datetime(2027, 3, 1, tzinfo=UTC)


def test_retention_cutoff_from_leap_day_falls_back_to_february_28() -> None:
    from datetime import datetime

    from apps.audit.models import retention_cutoff

    assert retention_cutoff(datetime(2028, 2, 29, tzinfo=UTC)) == datetime(2027, 2, 28, tzinfo=UTC)


def test_event_exactly_one_calendar_year_old_is_kept_on_leap_window() -> None:
    from datetime import datetime

    from apps.audit.models import retention_cutoff

    cutoff = retention_cutoff(datetime(2028, 3, 1, tzinfo=UTC))
    kept = SecurityEvent.objects.create(
        event_type=EventType.LOGIN, success=True, created_at=cutoff + timedelta(hours=12)
    )
    SecurityEvent.objects.create(
        event_type=EventType.LOGIN, success=True, created_at=cutoff - timedelta(seconds=1)
    )
    purge_expired(datetime(2028, 3, 1, tzinfo=UTC))
    assert SecurityEvent.objects.filter(pk=kept.pk).exists()
    assert SecurityEvent.objects.count() == 1


def test_manager_has_no_public_purge_method() -> None:
    assert not hasattr(SecurityEvent.objects, "purge_older_than")
