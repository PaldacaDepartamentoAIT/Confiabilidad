import pytest

from apps.core.models import DemoRecord


@pytest.mark.django_db
def test_demorecord_persists_and_reads_back() -> None:
    record = DemoRecord.objects.create(label="sample", source="seed")

    assert record.pk is not None
    stored = DemoRecord.objects.get(pk=record.pk)
    assert stored.label == "sample"
    assert stored.source == "seed"
    assert stored.created_at is not None
    assert str(stored) == "sample (seed)"
