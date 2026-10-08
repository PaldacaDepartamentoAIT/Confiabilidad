from django.apps import apps as global_apps
from django.apps.registry import Apps
from django.contrib.auth.management import create_permissions
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

SUPPORT_GROUP = "Soporte técnico"
SUPPORT_PERMISSIONS = [
    f"{action}_{model}"
    for action in ("view", "add", "change", "delete")
    for model in ("userterms", "marketingconsent")
]


def create_support_group(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    # En una base vacía los permisos se crean tras migrar; hay que crearlos antes de asignarlos.
    # Se pasa la AppConfig real (tiene models_module) y el estado de la migración en `apps`.
    create_permissions(global_apps.get_app_config("consents"), apps=apps, verbosity=0)
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    group, _ = group_model.objects.get_or_create(name=SUPPORT_GROUP)
    group.permissions.set(
        permission_model.objects.filter(
            content_type__app_label="consents", codename__in=SUPPORT_PERMISSIONS
        )
    )


def delete_support_group(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    apps.get_model("auth", "Group").objects.filter(name=SUPPORT_GROUP).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("consents", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_support_group, delete_support_group)]
