from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from apps.consents.models import PROTECTED_FIELDS, Terms


@admin.register(Terms)
class TermsAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    list_display = (
        "kind",
        "version",
        "locale",
        "published_at",
        "requires_reacceptance",
        "created_at",
        "has_acceptances_display",
    )
    list_filter = ("kind", "locale")
    search_fields = ("version",)

    @admin.display(boolean=True, description=_("Has acceptances"))
    def has_acceptances_display(self, obj: Terms) -> bool:
        return obj.has_acceptances()

    def get_readonly_fields(self, request: HttpRequest, obj: Terms | None = None) -> list[str]:
        readonly = ["created_at"]
        if obj is not None and obj.has_acceptances():
            readonly += PROTECTED_FIELDS
        return readonly

    def has_delete_permission(self, request: HttpRequest, obj: Terms | None = None) -> bool:
        if obj is not None and obj.has_acceptances():
            return False
        return bool(super().has_delete_permission(request, obj))

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Terms]) -> None:
        # El borrado masivo de Django no llama a delete(); se borra uno a uno para respetar RF-005.
        skipped = 0
        for document in queryset:
            try:
                document.delete()
            except ValidationError:
                skipped += 1
        if skipped:
            self.message_user(
                request,
                _("%(count)d documents of accepted versions were not deleted.")
                % {"count": skipped},
                messages.WARNING,
            )
