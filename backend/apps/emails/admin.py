from typing import Any

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from simple_history.admin import SimpleHistoryAdmin

from apps.emails.models import EmailTemplate

SUPPORT_GROUP = "Soporte técnico"


def is_support(request: HttpRequest) -> bool:
    # Solo el grupo «Soporte técnico» y los superusuarios, aunque otro staff tenga permisos (D-13).
    user = request.user
    if not (user.is_active and user.is_staff):
        return False
    return bool(user.is_superuser or user.groups.filter(name=SUPPORT_GROUP).exists())


@admin.register(EmailTemplate)
class EmailTemplateAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    list_display = ("kind", "locale", "subject", "updated_at")
    list_filter = ("kind", "locale")
    fields = ("kind", "locale", "subject", "body")
    readonly_fields = ("kind", "locale")

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_support(request)

    def has_view_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return is_support(request)

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return is_support(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def history_form_view(
        self, request: HttpRequest, object_id: str, version_id: str, extra_context: Any = None
    ) -> HttpResponse:
        # El historial se consulta, pero no se revierte desde el panel (RF-020).
        if request.method == "POST":
            raise PermissionDenied
        response: HttpResponse = super().history_form_view(
            request, object_id, version_id, extra_context
        )
        return response
