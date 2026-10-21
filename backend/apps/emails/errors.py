import smtplib
from enum import StrEnum


class Failure(StrEnum):
    TEMPORARY = "temporary"
    PERMANENT = "permanent"


def classify(error: BaseException) -> Failure:
    # Solo un rechazo 5xx del propio correo es definitivo; lo demás puede salir más tarde (D-03).
    if isinstance(error, smtplib.SMTPRecipientsRefused):
        codes = [code for code, _ in error.recipients.values()]
        return (
            Failure.PERMANENT if codes and all(code >= 500 for code in codes) else Failure.TEMPORARY
        )
    if isinstance(error, smtplib.SMTPSenderRefused | smtplib.SMTPDataError):
        return Failure.PERMANENT if error.smtp_code >= 500 else Failure.TEMPORARY
    return Failure.TEMPORARY
