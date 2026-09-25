from collections.abc import Iterator

import pytest
from celery.contrib.testing.worker import start_worker

from config.celery import app as celery_app


@pytest.fixture
def celery_worker() -> Iterator[None]:
    # Worker Celery real (broker Redis) para ejercitar el camino broker->worker.
    with start_worker(celery_app, perform_ping_check=False, shutdown_timeout=20):
        yield
