import importlib
import time
from collections.abc import Iterator

import pytest
from celery.contrib.testing.worker import start_worker
from django.apps import apps as global_apps
from django.core import mail
from django.db import transaction

from apps.emails import outbox
from apps.emails.models import OutboundEmail
from config.celery import app as celery_app


@pytest.fixture
def celery_worker() -> Iterator[None]:
    # Worker Celery real (broker Redis), como en `core`: el correo sale por el camino broker→worker.
    with start_worker(celery_app, perform_ping_check=False, shutdown_timeout=20):
        yield


@pytest.mark.django_db(transaction=True)
def test_a_queued_notice_is_delivered_by_the_real_worker(celery_worker: None) -> None:
    migration = importlib.import_module("apps.emails.migrations.0002_initial_templates")
    migration.create_initial_templates(global_apps, None)

    with transaction.atomic():
        email = outbox.enqueue(
            kind="password_changed",
            recipient="ana@example.com",
            locale="en",
            context={"name": "Ana"},
        )
    assert email is not None

    deadline = time.monotonic() + 15
    while OutboundEmail.objects.filter(pk=email.pk).exists() and time.monotonic() < deadline:
        time.sleep(0.2)

    assert not OutboundEmail.objects.filter(pk=email.pk).exists()
    assert [message.subject for message in mail.outbox] == ["Your password has changed"]
