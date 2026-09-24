from django.db import models


class DemoRecord(models.Model):
    # Registro desechable para probar la infraestructura (S-02).
    label = models.CharField(max_length=100)
    source = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.label} ({self.source})"
