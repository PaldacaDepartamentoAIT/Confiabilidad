from typing import Any

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_companies",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")

    def __str__(self) -> str:
        return f"{self.name} ({self.owner})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.name = self.name.strip()
        self.full_clean(validate_unique=False)
        super().save(*args, **kwargs)


def owns_company(user: Any) -> bool:
    return Company.objects.filter(owner=user).exists()
