from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.audit.models import SecurityEvent


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("created_at", "event_type", "success", "ip", "user_email_hash")
    list_filter = ("event_type", "success", "created_at")
    search_fields = ("ip", "user_email_hash")
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

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_view_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return request.user.has_perm("audit.view_securityevent")

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
