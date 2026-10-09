from django.core.exceptions import ValidationError
from django.core.management.base import OutputWrapper


def show_code(stdout: OutputWrapper, public_id: str, code: str) -> None:
    stdout.write(f"public_id: {public_id}\ncode: {code}")


def format_validation_error(error: ValidationError) -> str:
    if not hasattr(error, "error_dict"):
        return "\n".join(error.messages)
    return "\n".join(
        f"{field}: {message}"
        for field, messages in error.message_dict.items()
        for message in messages
    )
