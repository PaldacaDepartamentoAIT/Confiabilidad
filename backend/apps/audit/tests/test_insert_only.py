import pytest

from apps.audit.models import EventType, InsertOnlyError, SecurityEvent

pytestmark = pytest.mark.django_db


def _create() -> SecurityEvent:
    return SecurityEvent.objects.create(event_type=EventType.LOGIN, success=True)


def test_creating_events_still_works() -> None:
    event = _create()
    assert SecurityEvent.objects.filter(pk=event.pk).exists()


def test_saving_an_existing_event_raises_and_keeps_the_row() -> None:
    event = _create()
    event.success = False
    with pytest.raises(InsertOnlyError):
        event.save()
    assert SecurityEvent.objects.get(pk=event.pk).success is True


def test_deleting_an_event_instance_raises_and_keeps_the_row() -> None:
    event = _create()
    with pytest.raises(InsertOnlyError):
        event.delete()
    assert SecurityEvent.objects.filter(pk=event.pk).exists()


def test_queryset_update_raises_and_keeps_the_row() -> None:
    event = _create()
    with pytest.raises(InsertOnlyError):
        SecurityEvent.objects.filter(pk=event.pk).update(success=False)
    assert SecurityEvent.objects.get(pk=event.pk).success is True


def test_queryset_delete_raises_and_keeps_the_row() -> None:
    event = _create()
    with pytest.raises(InsertOnlyError):
        SecurityEvent.objects.filter(pk=event.pk).delete()
    assert SecurityEvent.objects.filter(pk=event.pk).exists()


def test_purge_context_allows_queryset_delete() -> None:
    from apps.audit.models import _purge_allowed

    event = _create()
    with _purge_allowed():
        SecurityEvent.objects.filter(pk=event.pk).delete()
    assert not SecurityEvent.objects.filter(pk=event.pk).exists()
