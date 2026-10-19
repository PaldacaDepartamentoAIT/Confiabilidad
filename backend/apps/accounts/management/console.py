from django.core.exceptions import ValidationError


def format_validation_error(error: ValidationError) -> str:
    if not hasattr(error, "error_dict"):
        return "\n".join(error.messages)
    return "\n".join(
        f"{field}: {message}"
        for field, messages in error.message_dict.items()
        for message in messages
    )
