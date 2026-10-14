from django.apps import apps


def test_audit_app_is_installed() -> None:
    assert apps.is_installed("apps.audit")
    assert apps.get_app_config("audit").name == "apps.audit"
