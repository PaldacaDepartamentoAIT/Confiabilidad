import pytest

from apps.core.models import DemoRecord
from apps.core.tasks import record_ping


@pytest.mark.django_db(transaction=True)
def test_record_ping_runs_on_real_worker(celery_worker: None) -> None:
    result = record_ping.delay("worker-hello")
    pk = result.get(timeout=15)

    stored = DemoRecord.objects.get(pk=pk)
    assert stored.source == "task"
    assert stored.label == "worker-hello"
