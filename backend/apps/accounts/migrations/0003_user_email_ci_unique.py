import django.db.models.functions.text
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.utils.translation import gettext_lazy as _


def normalize_emails(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    User = apps.get_model("accounts", "User")
    users = list(User.objects.order_by("pk"))
    owners: dict[str, str] = {}
    collisions: list[str] = []
    for user in users:
        normalized = user.email.strip().lower()
        if normalized in owners:
            collisions.append(f"{owners[normalized]} / {user.email}")
        else:
            owners[normalized] = user.email
    if collisions:
        raise RuntimeError(
            _("Emails that differ only in case: %(pairs)s.") % {"pairs": "; ".join(collisions)}
        )
    for user in users:
        normalized = user.email.strip().lower()
        if user.email != normalized:
            user.email = normalized
            user.save(update_fields=["email"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_profile_fields")]

    operations = [
        migrations.RunPython(normalize_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("email"),
                name="accounts_user_email_ci_unique",
                violation_error_message="A user with this email already exists.",
            ),
        ),
    ]
