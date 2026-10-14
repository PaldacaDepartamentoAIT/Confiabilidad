import pytest
from django.contrib.auth.models import Permission

pytestmark = pytest.mark.django_db


def test_default_view_permission_exists_for_security_event() -> None:
    assert Permission.objects.filter(
        codename="view_securityevent", content_type__app_label="audit"
    ).exists()
