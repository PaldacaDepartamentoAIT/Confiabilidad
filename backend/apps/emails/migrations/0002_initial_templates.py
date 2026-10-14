from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# Textos iniciales de los siete tipos en los tres idiomas (RF-022). Soporte los edita desde el panel.
INITIAL_TEMPLATES: dict[tuple[str, str], tuple[str, str]] = {
    ("registration_code", "es"): (
        "Confirma tu correo para crear tu cuenta",
        "Hola, {{ name }}:\n\n"
        "Tu código para confirmar tu correo es:\n\n"
        "{{ code }}\n\n"
        "El código vence en {{ expires_in }}. Si cerraste la ventana, puedes continuar el "
        "registro desde este enlace:\n"
        "{{ link }}\n\n"
        "Si no intentaste crear una cuenta, ignora este correo.",
    ),
    ("registration_code", "pt-BR"): (
        "Confirme seu e-mail para criar sua conta",
        "Olá, {{ name }}:\n\n"
        "Seu código para confirmar seu e-mail é:\n\n"
        "{{ code }}\n\n"
        "O código vence em {{ expires_in }}. Se você fechou a janela, pode continuar o "
        "cadastro por este link:\n"
        "{{ link }}\n\n"
        "Se você não tentou criar uma conta, ignore este e-mail.",
    ),
    ("registration_code", "en"): (
        "Confirm your email to create your account",
        "Hi {{ name }},\n\n"
        "Your code to confirm your email is:\n\n"
        "{{ code }}\n\n"
        "The code expires in {{ expires_in }}. If you closed the window, you can continue "
        "signing up from this link:\n"
        "{{ link }}\n\n"
        "If you didn't try to create an account, ignore this email.",
    ),
    ("password_reset_code", "es"): (
        "Tu código para restablecer la contraseña",
        "Hola, {{ name }}:\n\n"
        "Tu código para restablecer la contraseña es:\n\n"
        "{{ code }}\n\n"
        "El código vence en {{ expires_in }}. Si cerraste la ventana, puedes continuar desde "
        "este enlace:\n"
        "{{ link }}\n\n"
        "Si no pediste restablecer tu contraseña, ignora este correo: tu contraseña no cambiará.",
    ),
    ("password_reset_code", "pt-BR"): (
        "Seu código para redefinir a senha",
        "Olá, {{ name }}:\n\n"
        "Seu código para redefinir a senha é:\n\n"
        "{{ code }}\n\n"
        "O código vence em {{ expires_in }}. Se você fechou a janela, pode continuar por este "
        "link:\n"
        "{{ link }}\n\n"
        "Se você não pediu para redefinir sua senha, ignore este e-mail: sua senha não será "
        "alterada.",
    ),
    ("password_reset_code", "en"): (
        "Your code to reset your password",
        "Hi {{ name }},\n\n"
        "Your code to reset your password is:\n\n"
        "{{ code }}\n\n"
        "The code expires in {{ expires_in }}. If you closed the window, you can continue from "
        "this link:\n"
        "{{ link }}\n\n"
        "If you didn't ask to reset your password, ignore this email: your password won't change.",
    ),
    ("account_exists", "es"): (
        "Ya tienes una cuenta con este correo",
        "Hola, {{ name }}:\n\n"
        "Alguien ha intentado crear una cuenta con este correo, pero ya tienes una. Puedes "
        "iniciar sesión con tu contraseña o, si no la recuerdas, restablecerla desde la pantalla "
        "de inicio de sesión.",
    ),
    ("account_exists", "pt-BR"): (
        "Você já tem uma conta com este e-mail",
        "Olá, {{ name }}:\n\n"
        "Alguém tentou criar uma conta com este e-mail, mas você já tem uma. Você pode entrar "
        "com sua senha ou, se não se lembrar dela, redefini-la na tela de login.",
    ),
    ("account_exists", "en"): (
        "You already have an account with this email",
        "Hi {{ name }},\n\n"
        "Someone tried to create an account with this email, but you already have one. You can "
        "sign in with your password or, if you don't remember it, reset it from the sign-in "
        "screen.",
    ),
    ("password_reset_done", "es"): (
        "Tu contraseña se ha restablecido",
        "Hola, {{ name }}:\n\nLa contraseña de tu cuenta se acaba de restablecer.",
    ),
    ("password_reset_done", "pt-BR"): (
        "Sua senha foi redefinida",
        "Olá, {{ name }}:\n\nA senha da sua conta acabou de ser redefinida.",
    ),
    ("password_reset_done", "en"): (
        "Your password has been reset",
        "Hi {{ name }},\n\nThe password of your account has just been reset.",
    ),
    ("password_changed", "es"): (
        "Tu contraseña ha cambiado",
        "Hola, {{ name }}:\n\nLa contraseña de tu cuenta se acaba de cambiar.",
    ),
    ("password_changed", "pt-BR"): (
        "Sua senha foi alterada",
        "Olá, {{ name }}:\n\nA senha da sua conta acabou de ser alterada.",
    ),
    ("password_changed", "en"): (
        "Your password has changed",
        "Hi {{ name }},\n\nThe password of your account has just been changed.",
    ),
    ("account_disabled", "es"): (
        "Tu cuenta se ha deshabilitado",
        "Hola, {{ name }}:\n\n"
        "Tu cuenta se acaba de deshabilitar y ya no se puede usar para iniciar sesión.",
    ),
    ("account_disabled", "pt-BR"): (
        "Sua conta foi desativada",
        "Olá, {{ name }}:\n\n"
        "Sua conta acabou de ser desativada e não pode mais ser usada para entrar.",
    ),
    ("account_disabled", "en"): (
        "Your account has been disabled",
        "Hi {{ name }},\n\nYour account has just been disabled and can no longer be used to sign in.",
    ),
    ("sessions_closed", "es"): (
        "Se han cerrado las sesiones de tu cuenta",
        "Hola, {{ name }}:\n\n"
        "Se acaban de cerrar de forma remota las sesiones abiertas de tu cuenta. Tendrás que "
        "volver a iniciar sesión en tus dispositivos.",
    ),
    ("sessions_closed", "pt-BR"): (
        "As sessões da sua conta foram encerradas",
        "Olá, {{ name }}:\n\n"
        "As sessões abertas da sua conta acabaram de ser encerradas remotamente. Você precisará "
        "entrar novamente nos seus dispositivos.",
    ),
    ("sessions_closed", "en"): (
        "Your account's sessions have been closed",
        "Hi {{ name }},\n\n"
        "The open sessions of your account have just been closed remotely. You'll need to sign "
        "in again on your devices.",
    ),
}


def create_initial_templates(apps: Apps, schema_editor: BaseDatabaseSchemaEditor | None) -> None:
    # Idempotente: no pisa una plantilla ya editada por soporte.
    template_model = apps.get_model("emails", "EmailTemplate")
    for (kind, locale), (subject, body) in INITIAL_TEMPLATES.items():
        template_model.objects.get_or_create(
            kind=kind, locale=locale, defaults={"subject": subject, "body": body}
        )


def delete_initial_templates(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    # En el estado de las migraciones el modelo no tiene el bloqueo de borrado del panel.
    apps.get_model("emails", "EmailTemplate").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("emails", "0001_initial")]

    operations = [migrations.RunPython(create_initial_templates, delete_initial_templates)]
