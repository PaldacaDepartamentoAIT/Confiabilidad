from django.dispatch import Signal

from apps.accounts import signals

SIGNAL_NAMES = {
    "pending_registration_requested",
    "registration_code_sent",
    "registration_code_verified",
    "account_created",
    "password_reset_code_sent",
    "password_reset_code_verified",
    "password_reset_completed",
    "profile_edited",
    "account_disabled",
}


def test_all_account_signals_are_declared() -> None:
    for name in SIGNAL_NAMES:
        assert isinstance(getattr(signals, name), Signal), name


def test_signals_deliver_email_and_success_arguments() -> None:
    received: list[dict[str, object]] = []

    def receiver(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    signals.account_created.connect(receiver, weak=False)
    try:
        signals.account_created.send(sender=object, email="ana@x.com", success=True)
    finally:
        signals.account_created.disconnect(receiver)

    assert received == [{"email": "ana@x.com", "success": True, "signal": signals.account_created}]
