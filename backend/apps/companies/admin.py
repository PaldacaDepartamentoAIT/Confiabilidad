from django.contrib import admin

from apps.companies.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin[Company]):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__email")
    raw_id_fields = ("owner",)
    readonly_fields = ("created_at",)
