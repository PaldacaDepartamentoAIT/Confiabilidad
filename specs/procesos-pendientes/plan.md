# Plan: procesos-pendientes
Estado: aprobado

## Módulos
### M-01 Modelo `PendingRegistration` (`apps/accounts/models.py`)
Responsabilidad: guardar el registro pendiente; normalizar el correo como `User`; validar correo,
nombre, fecha y país con `validators.py`; rechazar el guardado si el correo ya tiene cuenta;
calcular si está caducado o bloqueado.
RF: RF-001, RF-002, RF-003, RF-004, RF-011

### M-02 Códigos (`apps/accounts/codes.py`)
Responsabilidad: generar el código de 6 dígitos y el identificador público, calcular la huella con
el secreto vigente y verificarla, aceptando también el secreto anterior durante la transición.
RF: RF-007, RF-008, RF-015

### M-03 Servicio de registro (`apps/accounts/registration.py`)
Responsabilidad: operaciones `start`, `verify`, `resend`, `complete` y `purge_expired`, cada una
en una transacción. Es la única puerta que usarán los comandos ahora y la API después.
RF: RF-005, RF-009, RF-010, RF-011, RF-012, RF-013, RF-016, RF-017, RF-020

### M-04 Configuración (`config/settings.py`, `apps/accounts/conf.py`, `.env.example`)
Responsabilidad: límites con valores por defecto (5 intentos, 15 min, 15 min, 1 h, 1 h, 2 s),
ajustables por variable de entorno, y el secreto de los códigos con su secreto anterior.
RF: RF-019, RF-015

### M-05 Política de contraseñas (`config/settings.py`, `apps/accounts/password_validation.py`)
Responsabilidad: `AUTH_PASSWORD_VALIDATORS` con longitud 12, similitud con `email` y `name`,
contraseñas comunes y un validador propio de contraseñas filtradas contra el servicio de rangos de
Have I Been Pwned.
RF: RF-022

### M-06 Comando `manage.py registration` (`management/commands/registration.py`)
Responsabilidad: subcomandos `start`, `verify`, `resend`, `complete` y `purge`, que solo llaman a
M-03 y muestran el `public_id`, el código emitido o el error.
RF: RF-023, RF-013

### M-07 Migración `0005_pendingregistration`
Responsabilidad: crear la tabla con las restricciones únicas de `public_id` y `Lower(email)`.
RF: RF-003, RF-007 (CF-1)

## Modelo de datos
`accounts.PendingRegistration`:
- `email` EmailField + `UniqueConstraint(Lower("email"))` (como `User`).
- `name` CharField(150), `birthdate` DateField, `country` CharField(2).
- `public_id` CharField(64), único.
- `code_hash` CharField(64): HMAC-SHA256 en hexadecimal.
- `code_expires_at` DateTimeField.
- `failed_attempts` PositiveSmallIntegerField, por defecto 0.
- `code_validated_at` DateTimeField, nulo mientras no se valide.
- `created_at` DateTimeField al crear.

Sin historial (`simple-history`): son datos de un proceso que se borran al terminar.
La caducidad no se guarda; se calcula: mín(`code_expires_at` + gracia, `created_at` + vida máxima).

## Decisiones
### D-01 Huella del código
Elegida: HMAC-SHA256 con un secreto del servidor sobre `public_id` + código, comparada en tiempo
constante.
Descartada: hash lento de contraseña (PBKDF2/Argon2) sin secreto.
Motivo: un código de 6 dígitos tiene 1 millón de valores; cualquier hash sin secreto se rompe por
fuerza bruta con la base de datos en la mano (RF-008). El HMAC exige además el secreto, y atar la
huella al `public_id` impide reutilizarla en otro proceso.

### D-02 Secreto y rotación
Elegida: variable `REGISTRATION_CODE_SECRET` (por defecto, `SECRET_KEY`, para que desarrollo y CI
funcionen igual), más `REGISTRATION_CODE_SECRET_PREVIOUS` y `REGISTRATION_CODE_SECRET_ROTATED_AT`:
el anterior se acepta hasta `ROTATED_AT` + periodo de transición.
Descartada: guardar en cada fila qué versión de secreto se usó.
Motivo: cumple RF-015 sin columnas extra; los procesos viven como mucho 1 hora, así que basta con
probar dos secretos. En producción el secreto va cifrado con SOPS (P-01): queda en `HUMAN_TODO`.

### D-03 Identificador público y código
Elegida: `secrets.token_urlsafe(32)` (256 bits) para `public_id` y `secrets.randbelow(10**6)`,
rellenado a 6 dígitos, para el código.
Descartada: UUID4 y `random`.
Motivo: `secrets` es criptográficamente seguro; `token_urlsafe` va bien en URL (S-06, futura API).

### D-04 Crear la cuenta
Elegida: dentro de una transacción, `User.objects.create_user` con los datos del registro y la
contraseña, `EmailAddress.objects.create(..., verified=True, primary=True)` de allauth y borrar el
registro pendiente.
Descartada: `adapter.confirm_email` de allauth.
Motivo: D-01 del spike permite usar los gestores de los modelos públicos de allauth, y
`confirm_email` exige una petición con sesión (C-14), que no existe en consola. La transacción
cumple el "en una sola operación" de RF-020.

### D-05 Política de contraseñas global
Elegida: cambiar `AUTH_PASSWORD_VALIDATORS` del proyecto (longitud 12, similitud con
`("email", "name")`, comunes, filtradas) y validar en `complete` con un `User` sin guardar que
lleva el correo y el nombre del registro pendiente.
Descartada: una política solo para el registro.
Motivo: una única política para todo el sistema; el futuro cambio de contraseña (S-11) la hereda.
Se mantiene `NumericPasswordValidator`, que ya existía: rechaza contraseñas solo numéricas y no
contradice RF-022. *Efecto:* el signup de allauth, todavía expuesto, también la aplica.

### D-06 Contraseñas filtradas sin dependencias ni red en los tests
Elegida: validador propio con `urllib` de la librería estándar contra
`https://api.pwnedpasswords.com/range/<5 caracteres del SHA-1>` (con la cabecera `Add-Padding`),
con tiempo máximo configurable. Si falla, aviso en el log y se acepta (S-09). Un ajuste
`PWNED_PASSWORDS_ENABLED` lo apaga; los tests lo apagan por defecto y prueban el validador
simulando la respuesta.
Descartada: un paquete externo (p. ej. `pwnedpasswords`).
Motivo: no añade dependencias (AGENTS.md); la suite no depende de internet ni de un servicio
externo.

### D-07 Tiempo en los tests
Elegida: el servicio usa `timezone.now()`; los tests mueven las fechas guardadas
(`created_at`, `code_expires_at`) con `update()` para simular el paso del tiempo.
Descartada: `freezegun` u otra librería de reloj.
Motivo: no añade dependencias y prueba la caducidad igual.

### D-08 Concurrencia
Elegida: `start` bloquea la fila existente con `select_for_update` y, si dos altas simultáneas
chocan en la restricción única del correo, trata la segunda como registro repetido (RF-005).
Descartada: confiar solo en el orden de llegada.
Motivo: RF-003 lo garantiza la base de datos; el servicio no debe devolver un error de base de
datos.

### D-09 Comando con subcomandos
Elegida: un único `manage.py registration <start|verify|resend|complete|purge>`; `complete` pide
la contraseña sin eco (`getpass`) o la acepta con `--password` para scripts y tests.
Descartada: cinco comandos sueltos.
Motivo: el proceso se descubre en un solo `--help`. *Riesgo:* `--password` queda en el historial
de la consola; se documenta.

### D-10 Correo con cuenta en `start`
Elegida: el servicio devuelve un resultado "cuenta existente" sin guardar nada, y el comando lo
muestra tal cual.
Descartada: lanzar una excepción.
Motivo: la futura API debe responder igual en los tres casos (respuesta 8); un resultado tipado se
lo pone fácil. En consola no hay riesgo de enumeración (S-10).

## Estrategia de tests
- Unitario (`test_codes.py`): formato del código y del `public_id`, la huella no contiene el
  código, verificación en tiempo constante, rotación dentro y fuera de la transición (RF-007,
  RF-008, RF-015).
- Modelo (`test_pending_registration_model.py`): validación y normalización, rechazo con cuenta
  existente, unicidad por `bulk_create` (RF-001…RF-004).
- Servicio (`test_registration_service.py`): el ciclo completo y cada rama — repetido, reenvío,
  intentos y bloqueo, caducidad por gracia y por vida máxima, código ya validado, cuenta creada
  entretanto, purga, caducados del mismo correo, límites cambiados con `override_settings`
  (RF-005, RF-009…RF-013, RF-016, RF-017, RF-019, RF-020).
- Contraseñas (`test_password_policy.py`): cada regla, con la respuesta del servicio simulada,
  incluido el tiempo agotado (RF-022).
- Comando (`test_registration_command.py`): recorrido completo con `call_command` y su salida
  (RF-023, RF-013).
- Login: la cuenta creada inicia sesión por app (cierra el ciclo con allauth).
- Mutaciones en cada tarea, como en `usuario-personalizado`.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-07 | modelo |
| RF-002 | M-01 | modelo |
| RF-003 | M-01, M-07, M-03 (D-08) | modelo (bulk) + servicio |
| RF-004 | M-01, M-03 | modelo + servicio |
| RF-005 | M-03 | servicio |
| RF-007 | M-02, M-07 | unitario + modelo |
| RF-008 | M-02 | unitario |
| RF-009 | M-03 | servicio |
| RF-010 | M-03, M-04 | servicio |
| RF-011 | M-01, M-03 | servicio |
| RF-012 | M-03 | servicio |
| RF-013 | M-03, M-06 | servicio + comando |
| RF-015 | M-02, M-04 | unitario |
| RF-016 | M-03 | servicio |
| RF-017 | M-03 | servicio |
| RF-019 | M-04 | servicio + unitario |
| RF-020 | M-03 (D-04) | servicio + login |
| RF-022 | M-05 | contraseñas |
| RF-023 | M-06 | comando |

## RF sin cobertura
Ninguno (RF-006, RF-014, RF-018 y RF-021 son obsoletos).
