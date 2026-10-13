from collections.abc import Iterator
from datetime import date
from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.audit.models import SecurityEvent


def _first(value: str | list[str]) -> str:
    return value[0] if isinstance(value, list) else value


def _parse_day(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class CreatedDateRangeFilter(admin.SimpleListFilter):
    title = _("created at")
    parameter_name = "created_range"
    template = "admin/audit/filter_date_range.html"
    start_param = "desde"
    end_param = "hasta"

    def __init__(
        self, request: HttpRequest, params: dict[str, list[str]], model: type, model_admin: Any
    ) -> None:
        self._request = request
        self.start = _first(params.pop(self.start_param, ""))
        self.end = _first(params.pop(self.end_param, ""))
        super().__init__(request, params, model, model_admin)

    def expected_parameters(self) -> list[str | None]:
        return [self.start_param, self.end_param]

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return []

    def has_output(self) -> bool:
        return True

    def choices(self, changelist: Any) -> Iterator[Any]:
        return iter(())

    @property
    def hidden_fields(self) -> list[tuple[str, str]]:
        keys = {self.start_param, self.end_param, "p"}
        return [(key, str(value)) for key, value in self._request.GET.items() if key not in keys]

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        start = _parse_day(self.start)
        end = _parse_day(self.end)
        if start is not None:
            queryset = queryset.filter(created_at__date__gte=start)
        if end is not None:
            queryset = queryset.filter(created_at__date__lte=end)
        return queryset


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("created_at", "event_type", "success", "ip", "user_email_hash")
    list_filter = ("event_type", "success", CreatedDateRangeFilter)
    search_fields = ("ip", "=user_email_hash")
    readonly_fields = (
        "event_type",
        "created_at",
        "session_key",
        "ip",
        "user_agent",
        "user_email_hash",
        "success",
        "metadata",
    )

    def has_view_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return request.user.has_perm("audit.view_securityevent")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
