from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from apps.accounts import disable
from apps.accounts.models import User

SUPPORT_GROUP = "Soporte técnico"


def is_support(request: HttpRequest) -> bool:
    user = request.user
    if not (user.is_active and user.is_staff):
        return False
    return bool(user.is_superuser or user.groups.filter(name=SUPPORT_GROUP).exists())


class UserAdminForm(forms.ModelForm):  # type: ignore[type-arg]
    current_request: HttpRequest | None = None

    class Meta:
        model = User
        fields = (
            "email",
            "name",
            "birthdate",
            "country",
            "language",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data: dict[str, Any] = super().clean() or {}
        if not self.instance.pk:
            return cleaned_data
        was_active = (
            User.objects.filter(pk=self.instance.pk).values_list("is_active", flat=True).first()
        )
        next_active = bool(cleaned_data.get("is_active"))
        if was_active is False and next_active is True:
            request = self.current_request
            if request is None or not is_support(request):
                raise ValidationError(
                    _("Only Technical Support or superusers can reactivate disabled accounts."),
                    code="support_required",
                )
            if disable.is_retention_expired(self.instance):
                raise ValidationError(
                    _("The 12-month reactivation period has expired."),
                    code="reactivation_expired",
                )
        if (
            was_active is True
            and next_active is False
            and self.instance.is_superuser
            and not User.active.filter(is_superuser=True).exclude(pk=self.instance.pk).exists()
        ):
            raise ValidationError(
                _("Cannot deactivate the last active superuser."),
                code="last_superuser",
            )
        return cleaned_data


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):  # type: ignore[misc]
    form = UserAdminForm
    list_display = ("email", "name", "is_active", "disabled_at", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name")
    actions = ("reactivate_selected",)
    readonly_fields = ("date_joined", "last_login", "disabled_at")

    def get_readonly_fields(self, request: HttpRequest, obj: User | None = None) -> list[str]:
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            for field in ("is_staff", "is_superuser", "groups", "user_permissions"):
                if field not in readonly:
                    readonly.append(field)
        return readonly

    def get_form(
        self, request: HttpRequest, obj: User | None = None, change: bool = False, **kwargs: Any
    ) -> type[forms.ModelForm[Any]]:
        base_form: type[UserAdminForm] = super().get_form(request, obj, change, **kwargs)

        class _BoundUserAdminForm(base_form):  # type: ignore[valid-type, misc]
            current_request = request

        bound: type[forms.ModelForm[Any]] = _BoundUserAdminForm
        return bound

    def has_module_permission(self, request: HttpRequest) -> bool:
        return is_support(request) or bool(super().has_module_permission(request))

    def has_view_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return is_support(request) or bool(super().has_view_permission(request, obj))

    def has_change_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        if obj is not None and not obj.is_active and not is_support(request):
            return False
        return is_support(request) or bool(super().has_change_permission(request, obj))

    def has_add_permission(self, request: HttpRequest) -> bool:
        return bool(request.user.is_superuser)

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return bool(request.user.is_superuser)

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions: dict[str, Any] = dict(super().get_actions(request))
        if not is_support(request):
            actions.pop("reactivate_selected", None)
        return actions

    @admin.action(description=_("Reactivate selected accounts"))
    def reactivate_selected(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        if not is_support(request):
            raise PermissionDenied
        reactivated = 0
        expired = 0
        for account in queryset.filter(is_active=False):
            result = disable.reactivate_account(account)
            if isinstance(result, disable.AccountReactivated):
                reactivated += 1
            elif isinstance(result, disable.ReactivationExpired):
                expired += 1
        if reactivated:
            self.message_user(
                request,
                _("%(count)d accounts were reactivated.") % {"count": reactivated},
                messages.SUCCESS,
            )
        if expired:
            self.message_user(
                request,
                _("%(count)d accounts exceeded the 12-month reactivation period.")
                % {"count": expired},
                messages.ERROR,
            )

    def history_form_view(
        self, request: HttpRequest, object_id: str, version_id: str, extra_context: Any = None
    ) -> HttpResponse:
        if request.method == "POST":
            raise PermissionDenied
        response: HttpResponse = super().history_form_view(
            request, object_id, version_id, extra_context
        )
        return response
