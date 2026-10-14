from django.dispatch import Signal

# Argumentos comunes: email (str) y success (bool). Ver el plan de auditoría (M-08).
pending_registration_requested = Signal()
registration_code_sent = Signal()
registration_code_verified = Signal()
account_created = Signal()
password_reset_code_sent = Signal()
password_reset_code_verified = Signal()
password_reset_completed = Signal()
profile_edited = Signal()
account_disabled = Signal()
