from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self) -> None:
        from apps.accounts import codes, email_checks
        from apps.emails.delivery import register_code_check

        register_code_check(codes.Purpose.REGISTRATION, email_checks.registration_code_expiry)
        register_code_check(codes.Purpose.PASSWORD_RESET, email_checks.password_reset_code_expiry)
