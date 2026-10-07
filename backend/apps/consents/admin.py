from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from apps.consents.models import PROTECTED_FIELDS, MarketingConsent, Terms, UserTerms

SUPPORT_GROUP = "Soporte técnico"


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


class _SupportAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    # Solo el grupo «Soporte técnico» y los superusuarios, aunque otro staff tenga permisos (D-09).
    readonly_fields = ("user_email_hash",)
    raw_id_fields = ("user",)
    actions = ("revoke_selected",)

    def _is_support(self, request: HttpRequest) -> bool:
        user = request.user
        if not (user.is_active and user.is_staff):
            return False
        return bool(user.is_superuser or user.groups.filter(name=SUPPORT_GROUP).exists())

    def has_module_permission(self, request: HttpRequest) -> bool:
        return self._is_support(request)

    def has_view_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return self._is_support(request)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return self._is_support(request)

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return self._is_support(request)

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return self._is_support(request)

    def get_form(
        self, request: HttpRequest, obj: Any = None, change: bool = False, **kwargs: Any
    ) -> type[ModelForm[Any]]:
        form: type[ModelForm[Any]] = super().get_form(request, obj, change, **kwargs)
        # Al crear hace falta un usuario para calcular la huella (RF-012).
        form.base_fields["user"].required = obj is None
        return form

    @admin.action(description=_("Revoke selected"))
    def revoke_selected(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        for record in queryset.filter(revoked_at__isnull=True):
            self._revoke(record)

    def _revoke(self, record: Any) -> None:
        record.revoked_at = timezone.now()
        record.save()


@admin.register(UserTerms)
class UserTermsAdmin(_SupportAdmin):
    list_display = ("terms", "user", "user_email_hash", "terms_accepted_at", "revoked_at")
    list_filter = ("terms__locale",)
    search_fields = ("user__email", "user_email_hash")


@admin.register(MarketingConsent)
class MarketingConsentAdmin(_SupportAdmin):
    list_display = ("terms", "user", "user_email_hash", "granted", "granted_at", "revoked_at")
    list_filter = ("granted", "terms__locale")
    search_fields = ("user__email", "user_email_hash")

    def _revoke(self, record: Any) -> None:
        record.granted = False
        super()._revoke(record)
