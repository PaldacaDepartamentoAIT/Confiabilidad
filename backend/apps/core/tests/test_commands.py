from collections.abc import Iterator
from io import StringIO

import pytest
from django.core.cache import cache
from django.core.management import call_command

from apps.core.models import DemoRecord


@pytest.fixture
def eager_celery() -> Iterator[None]:
    from config.celery import app

    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    yield
    app.conf.task_always_eager = False
    app.conf.task_eager_propagates = False


@pytest.mark.django_db
def test_demo_seed_creates_record() -> None:
    out = StringIO()
    call_command("demo_seed", stdout=out)

    assert DemoRecord.objects.filter(source="seed").count() == 1
    assert "total=1" in out.getvalue()


def test_demo_cache_roundtrip() -> None:
    out = StringIO()
    call_command("demo_cache", stdout=out)

    assert cache.get("demo-command-key") == "demo-command-value"
    assert "demo-command-value" in out.getvalue()


@pytest.mark.django_db
def test_demo_task_enqueues_and_runs(eager_celery: None) -> None:
    call_command("demo_task")

    assert DemoRecord.objects.filter(source="task").exists()
