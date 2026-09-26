import pytest
from django.core.management import call_command

from apps.accounts.models import User

SEED_EMAIL = "test@example.com"


@pytest.mark.django_db
def test_seed_creates_test_user_idempotently() -> None:
    call_command("seed_test_user")
    call_command("seed_test_user")

    assert User.objects.filter(email=SEED_EMAIL).count() == 1
