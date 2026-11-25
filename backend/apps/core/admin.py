from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.core.models import MaintenanceAlert, MaintenanceTaskStatus


class _ReadOnlyMaintenanceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class AlertStateFilter(admin.SimpleListFilter):
    title = _("state")
    parameter_name = "state"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("open", str(_("Open"))), ("resolved", str(_("Resolved")))]

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        if self.value() == "open":
            return queryset.filter(resolved_at__isnull=True)
        if self.value() == "resolved":
            return queryset.filter(resolved_at__isnull=False)
        return queryset


@admin.register(MaintenanceTaskStatus)
class MaintenanceTaskStatusAdmin(_ReadOnlyMaintenanceAdmin):
    list_display = (
        "task_name",
        "status",
        "deleted_count",
        "started_at",
        "finished_at",
        "error_summary",
    )
    list_filter = ("task_name", "status")
    readonly_fields = list_display


@admin.register(MaintenanceAlert)
class MaintenanceAlertAdmin(_ReadOnlyMaintenanceAdmin):
    list_display = ("task_name", "created_at", "open_state", "resolved_at", "error_summary")
    list_filter = ("task_name", AlertStateFilter)
    readonly_fields = ("task_name", "created_at", "resolved_at", "error_summary")

    @admin.display(boolean=True, description=_("open"))
    def open_state(self, obj: MaintenanceAlert) -> bool:
        return obj.is_open
