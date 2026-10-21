from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# Las plantillas de 0002 se crean sin historial; sin este registro, el primer cambio desde el panel
# perdería el texto anterior (RF-020).
INITIAL_REASON = "Initial text"


def record_initial_history(apps: Apps, schema_editor: BaseDatabaseSchemaEditor | None) -> None:
    # Idempotente: una plantilla que ya tiene historial no se toca.
    template_model = apps.get_model("emails", "EmailTemplate")
    history_model = apps.get_model("emails", "HistoricalEmailTemplate")
    for template in template_model.objects.all():
        if history_model.objects.filter(id=template.id).exists():
            continue
        history_model.objects.create(
            id=template.id,
            kind=template.kind,
            locale=template.locale,
            subject=template.subject,
            body=template.body,
            updated_at=template.updated_at,
            history_date=template.updated_at,
            history_type="+",
            history_change_reason=INITIAL_REASON,
        )


def forget_initial_history(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    apps.get_model("emails", "HistoricalEmailTemplate").objects.filter(
        history_type="+", history_change_reason=INITIAL_REASON
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("emails", "0003_support_permissions")]

    operations = [migrations.RunPython(record_initial_history, forget_initial_history)]
