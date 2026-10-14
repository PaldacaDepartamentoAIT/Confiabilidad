from typing import Any

from django.apps import apps as global_apps
from django.apps.registry import Apps
from django.contrib.auth.management import create_permissions
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

SUPPORT_GROUP = "Soporte técnico"
SUPPORT_PERMISSIONS = [
    "view_emailtemplate",
    "change_emailtemplate",
    "view_failedemail",
    "delete_failedemail",
]


def _permissions(apps: Apps) -> list[Any]:
    permission_model = apps.get_model("auth", "Permission")
    return list(
        permission_model.objects.filter(
            content_type__app_label="emails", codename__in=SUPPORT_PERMISSIONS
        )
    )


def grant_support_permissions(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    # En una base vacía los permisos se crean tras migrar; hay que crearlos antes de asignarlos.
    create_permissions(global_apps.get_app_config("emails"), apps=apps, verbosity=0)
    group, _ = apps.get_model("auth", "Group").objects.get_or_create(name=SUPPORT_GROUP)
    group.permissions.add(*_permissions(apps))


def revoke_support_permissions(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    group = apps.get_model("auth", "Group").objects.filter(name=SUPPORT_GROUP).first()
    if group is not None:
        group.permissions.remove(*_permissions(apps))


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("consents", "0002_support_group"),
        ("emails", "0002_initial_templates"),
    ]

    operations = [migrations.RunPython(grant_support_permissions, revoke_support_permissions)]
