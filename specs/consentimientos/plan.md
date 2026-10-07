# Plan: consentimientos
Estado: borrador

## Módulos
### M-01 App `consents` (`apps/consents/`, `config/settings.py`)
Responsabilidad: app nueva con su `AppConfig`, registrada en `INSTALLED_APPS`. Contiene todo lo de
esta feature y depende de `accounts` solo por `settings.AUTH_USER_MODEL`.
RF: — (estructura; D-01)

### M-02 Validadores (`apps/consents/validators.py`)
Responsabilidad: idiomas permitidos (`es`, `pt-BR`, `en`), formato de la versión y rechazo de
etiquetas HTML en el contenido.
RF: RF-001

### M-03 Modelo `Terms` (`apps/consents/models.py`)
Responsabilidad: documento legal versionado. Valida campos (M-02), unicidad de versión sin
distinguir mayúsculas, coherencia de `requires_reacceptance` entre idiomas, e inmutabilidad de la
versión aceptada en `save()` y `delete()`.
RF: RF-001, RF-002, RF-005, RF-017

### M-04 Vigencia (`apps/consents/versions.py`)
Responsabilidad: calcular las versiones en vigor de un tipo (las que tienen los tres idiomas
publicados, con su fecha de entrada en vigor y si exigen nueva aceptación), la versión vigente y
el documento vigente en un idioma.
RF: RF-003, RF-017

### M-05 Huella del correo (`apps/consents/hashing.py`, `conf.py`)
Responsabilidad: HMAC-SHA256 del correo normalizado con el secreto `CONSENT_EMAIL_HASH_SECRET`.
RF: RF-012

### M-06 Modelos `UserTerms` y `MarketingConsent` (`apps/consents/models.py`)
Responsabilidad: pruebas de aceptación y consentimiento. Calculan la huella al crearse o al
cambiar de usuario, exigen usuario al crear, comprueban que el documento es del tipo correcto y
llevan las restricciones de unicidad y coherencia de D-05.
RF: RF-007, RF-010, RF-011, RF-012, RF-013, RF-018

### M-07 Servicio de consentimientos (`apps/consents/services.py`)
Responsabilidad: operaciones `accept_terms`, `grant_marketing`, `revoke_marketing` y
`consent_status`, cada una en una transacción. Es la única puerta para los comandos ahora y la
API después.
RF: RF-006, RF-007, RF-008, RF-009, RF-010, RF-014, RF-015

### M-08 Panel de administración (`apps/consents/admin.py`, `config/settings.py`)
Responsabilidad: `TermsAdmin` con permisos de modelo, campos de solo lectura y sin borrado en
versiones aceptadas; `UserTermsAdmin` y `MarketingConsentAdmin` solo para «Soporte técnico» y
superusuarios, con la huella de solo lectura y la acción «Revocar»; historial visible en los tres
sin opción de revertir (`SIMPLE_HISTORY_REVERT_DISABLED`).
RF: RF-004, RF-005, RF-010, RF-018, RF-019, RF-020

### M-09 Historial (`HistoricalRecords` en los tres modelos)
Responsabilidad: una versión por alta, cambio o borrado, con el autor que ya rellena
`HistoryRequestMiddleware`.
RF: RF-020

### M-10 Comando `manage.py consents` (`management/commands/consents.py`)
Responsabilidad: subcomandos `current`, `accept-terms`, `grant-marketing`, `revoke-marketing` y
`status`, que solo llaman a M-04 y M-07 y muestran el resultado o el error.
RF: RF-016

### M-11 Migraciones `0001_initial` y `0002_support_group`
Responsabilidad: crear las tres tablas y sus históricos con las restricciones de D-05, y el grupo
«Soporte técnico» con los permisos de `UserTerms` y `MarketingConsent`.
RF: RF-002, RF-007, RF-011, RF-019 (CF-1)

### M-12 Configuración (`config/settings.py`, `backend/.env.example`, `HUMAN_TODO.md`)
Responsabilidad: `CONSENT_EMAIL_HASH_SECRET` (por defecto `SECRET_KEY`, como D-02 de
`procesos-pendientes`) y el aviso para fijarlo en producción con SOPS.
RF: RF-012

## Modelo de datos
`consents.Terms` (nombre del diagrama; guarda los dos tipos):
- `kind` CharField(20), opciones `terms` | `marketing`.
- `content` TextField (Markdown sin HTML).
- `version` CharField(20), patrón `^[A-Za-z0-9.-]{1,20}$`.
- `locale` CharField(5), opciones `es` | `pt-BR` | `en`.
- `requires_reacceptance` BooleanField, por defecto `True`; en `marketing` siempre `False` (D-07).
- `published_at` DateTimeField, nulo = borrador.
- `created_at` DateTimeField al crear.
- `UniqueConstraint(kind, Lower(version), locale)`.
- `history = HistoricalRecords()`.

`consents.UserTerms`:
- `user` FK a `User`, `null=True`, `on_delete=SET_NULL`.
- `terms` FK a `Terms`, `on_delete=PROTECT`, limitado a `kind=terms`.
- `user_email_hash` CharField(64), `editable=False`.
- `terms_accepted_at` DateTimeField, por defecto ahora.
- `revoked_at` DateTimeField, nulo.
- `UniqueConstraint(user, terms, condition=Q(revoked_at__isnull=True))`.
- `history = HistoricalRecords()`.

`consents.MarketingConsent`:
- `user` FK a `User`, `null=True`, `on_delete=SET_NULL`.
- `terms` FK a `Terms`, `on_delete=PROTECT`, limitado a `kind=marketing`.
- `user_email_hash` CharField(64), `editable=False`.
- `granted` BooleanField, por defecto `True`.
- `granted_at` DateTimeField, por defecto ahora.
- `revoked_at` DateTimeField, nulo.
- `UniqueConstraint(user, condition=Q(granted=True))`.
- `CheckConstraint`: `granted=True` si y solo si `revoked_at` es nulo.
- `history = HistoricalRecords()`.

Lo que no se guarda: la versión vigente, la fecha de entrada en vigor y si un usuario tiene los
términos aceptados se calculan (M-04, M-07).

## Decisiones
### D-01 App propia
Elegida: app nueva `apps.consents`.
Descartada: añadir los modelos a `apps.accounts`.
Motivo: `accounts` ya concentra usuario, registro y contraseñas; los consentimientos son otro
dominio con su panel, su comando y sus migraciones. Solo depende del usuario por FK.

### D-02 Una tabla para términos y marketing
Elegida: `Terms` con `kind`, como se decidió en la entrevista (pregunta 2).
Descartada: una tabla `MarketingTerms` aparte.
Motivo: comparten campos, reglas de vigencia, inmutabilidad, panel e historial; duplicarlas
duplicaría el código y los tests.

### D-03 Vigencia calculada en consulta
Elegida: agrupar por `(kind, Lower(version))` los documentos con `published_at <= ahora`, quedarse
con los grupos de 3 documentos (uno por idioma, garantizado por la unicidad) y tomar
`Max(published_at)` como entrada en vigor; la vigente es la de mayor entrada en vigor y, a
igualdad, la de mayor `Max(created_at)`.
Descartada: guardar una marca de "vigente" o una fecha de entrada en vigor en cada fila.
Motivo: una marca guardada se desincroniza cuando llega una fecha de publicación futura sin que
nadie guarde nada. Calcularla siempre da la respuesta correcta en el momento de la consulta.

### D-04 Inmutabilidad en el modelo y en el panel
Elegida: `Terms.save()` compara con la fila guardada y rechaza con `ValidationError` el cambio de
campos protegidos si algún documento de la versión (la guardada, no la nueva) tiene aceptaciones o
consentimientos; `Terms.delete()` rechaza el borrado en ese caso; el panel muestra esos campos de
solo lectura, oculta el botón de borrar y sustituye el borrado masivo por uno que pasa por
`delete()`. `PROTECT` en las FK lo garantiza además en la base de datos para el documento
aceptado.
Descartada: comprobarlo solo en el panel.
Motivo: RF-005 debe valer en consola y en código (criterio común de la spec). El borrado masivo de
Django no llama a `delete()`, por eso se sustituye en el panel. Cargas masivas y SQL quedan fuera
(S-10).

### D-05 Restricciones en la base de datos
Elegida: unicidades parciales (aceptación no revocada por usuario y documento; consentimiento
activo por usuario) y un `CheckConstraint` que liga `granted` con `revoked_at`.
Descartada: comprobarlo solo en el servicio.
Motivo: soporte también escribe desde el panel, y dos operaciones simultáneas podrían colarse.
PostgreSQL trata los `NULL` como distintos, así que las filas sin usuario (cuenta borrada) no
chocan entre sí (S-11).

### D-06 Huella con un secreto propio
Elegida: `CONSENT_EMAIL_HASH_SECRET`, por defecto `SECRET_KEY` en desarrollo y CI, sobre el correo
con `strip().lower()`; HMAC-SHA256 en hexadecimal.
Descartada: reutilizar `REGISTRATION_CODE_SECRET`.
Motivo: el secreto de los códigos está pensado para rotar (RF-015 de `procesos-pendientes`), y este
no puede hacerlo sin romper las huellas (S-09). En producción va cifrado con SOPS (P-01): se anota
en `HUMAN_TODO.md`, con el aviso de no cambiarlo nunca.

### D-07 `requires_reacceptance` por defecto
Elegida: `True` en términos; en marketing, `save()` lo fija a `False`.
Descartada: `False` por defecto.
Motivo: olvidarse de marcarlo debe errar hacia pedir otra aceptación, no hacia dar por aceptado un
texto nuevo. En marketing no tiene efecto (RF-001).

### D-08 Contenido sin HTML
Elegida: rechazar el contenido si contiene una etiqueta de apertura o cierre (`<p>`, `</a>`), un
comentario (`<!--`) o una declaración (`<!DOCTYPE`, `<?`); los enlaces automáticos de Markdown
(`<https://…>`) y los signos sueltos (`a < b`) se permiten.
Descartada: sanear el HTML al guardar.
Motivo: sanear exige una dependencia nueva y cambia en silencio el texto legal. Rechazar es
verificable y deja el texto igual a lo que se publica.

### D-09 Acceso de soporte técnico por grupo
Elegida: en `UserTermsAdmin` y `MarketingConsentAdmin`, los métodos `has_*_permission` exigen ser
superusuario o pertenecer al grupo «Soporte técnico». El grupo lleva además los permisos de modelo
de las dos tablas, creados por la migración de datos.
Descartada: solo permisos de modelo.
Motivo: con permisos sueltos, cualquier staff al que se le asignen podría gestionar las pruebas, y
RF-019 dice "solo el grupo". En una base vacía los permisos aún no existen al migrar: la migración
los crea con `create_permissions` antes de asignarlos.

### D-10 Concurrencia y repetición
Elegida: `accept_terms` y `grant_marketing` bloquean con `select_for_update` la fila relevante (la
aceptación no revocada o el consentimiento activo); si dos llamadas simultáneas chocan con la
unicidad de D-05, se devuelve la fila existente (RF-007, RF-009).
Descartada: confiar solo en el orden de llegada.
Motivo: igual que D-08 de `procesos-pendientes`: la regla la garantiza la base de datos y el
servicio no debe devolver un error de base de datos.

### D-11 Estado de términos
Elegida: `consent_status` toma las versiones de términos en vigor (D-03); la versión exigida es la
de mayor entrada en vigor entre las que tienen `requires_reacceptance` más la primera en vigor
(RF-017); el usuario tiene los términos aceptados si tiene una aceptación no revocada de un
documento cuya versión está en vigor con entrada en vigor ≥ la de la exigida. Sin versiones en vigor
devuelve "sin términos vigentes".
Descartada: comparar etiquetas de versión ("v10" > "v9").
Motivo: las etiquetas son texto libre sin orden; la fecha de entrada en vigor sí lo tiene.

### D-12 Errores del servicio
Elegida: `ValidationError` con `code` (`no_current_version`, `not_current_document`,
`wrong_kind`, `inactive_account`, `document_not_found`) y mensajes en inglés con `gettext_lazy`.
Descartada: excepciones propias por caso.
Motivo: es lo que ya usa `registration.py`, el comando lo muestra igual y la futura API de DRF lo
traduce a 400 sin código extra.

### D-13 Comando con subcomandos
Elegida: `manage.py consents <current|accept-terms|grant-marketing|revoke-marketing|status>`, con
el usuario por correo y el documento por `--version` y `--locale`.
Descartada: un comando por operación.
Motivo: como D-09 de `procesos-pendientes`: todo se descubre con un `--help`.

### D-14 Tiempo en los tests
Elegida: los tests fijan `published_at` en el pasado o en el futuro respecto a `timezone.now()`.
Descartada: `freezegun` u otra librería de reloj.
Motivo: no añade dependencias (D-07 de `procesos-pendientes`).

## Estrategia de tests
Todo en `apps/consents/tests/`, con una factoría `make_document` y `publish_version` (los tres
idiomas a la vez) y la factoría de usuarios de `accounts`. Prueba de mutación en cada tarea.
- Unitario (`test_validators.py`, `test_hashing.py`): idiomas, versión, HTML permitido y
  rechazado; la huella no contiene el correo, es estable, normaliza y cambia con otro secreto
  (RF-001, RF-012).
- Modelo (`test_terms_model.py`): validación, unicidad sin mayúsculas también por `bulk_create`,
  coherencia de `requires_reacceptance`, inmutabilidad de la versión entera en `save()` y
  `delete()`, `PROTECT` (RF-001, RF-002, RF-005, RF-017).
- Modelo (`test_acceptance_models.py`): huella al crear y al cambiar de usuario y no al cambiar el
  correo del usuario, usuario obligatorio al crear, tipo de documento, unicidades parciales y
  `CheckConstraint` también por `bulk_create`, conservación con `SET_NULL` al borrar la cuenta
  (RF-007, RF-011, RF-012, RF-013, RF-018).
- Vigencia (`test_versions.py`): falta un idioma, borrador, fecha futura, varias versiones, empate
  (RF-003).
- Servicio (`test_services.py`): aceptar y conceder con cada rechazo, repetición, sustitución,
  revocación sin activo, cuenta inactiva, estado con versiones que exigen o no nueva aceptación y
  aceptación en otro idioma (RF-006…RF-011, RF-014, RF-015, RF-017).
- Panel (`test_admin.py`, con el cliente de test y `force_login`): staff con y sin permisos de
  documentos, versión aceptada de solo lectura y sin borrado (también masivo), soporte frente a
  staff sin grupo, acción «Revocar», huella de solo lectura, historial con autor y sin revertir
  (RF-004, RF-005, RF-010, RF-018, RF-019, RF-020).
- Historial (`test_history.py`): alta, modificación y borrado en las tres tablas, conservado tras
  el borrado (RF-020).
- Comando (`test_consents_command.py`): cada subcomando con `call_command` y su salida (RF-016).
- Migraciones (`test_migrations.py`): el grupo existe con sus permisos tras migrar desde cero
  (RF-019, CF-1).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-02, M-03 | unitario + modelo |
| RF-002 | M-03, M-11 | modelo (bulk) |
| RF-003 | M-04 | vigencia |
| RF-004 | M-08 | panel |
| RF-005 | M-03 (D-04), M-08 | modelo + panel |
| RF-006 | M-07, M-04 | servicio |
| RF-007 | M-06, M-07, M-11 | modelo (bulk) + servicio |
| RF-008 | M-07, M-04 | servicio |
| RF-009 | M-07 | servicio |
| RF-010 | M-06, M-07, M-08 | servicio + panel |
| RF-011 | M-06, M-11 | modelo (bulk) + servicio |
| RF-012 | M-05, M-06, M-12 | unitario + modelo |
| RF-013 | M-06 | modelo |
| RF-014 | M-07 | servicio |
| RF-015 | M-07 (D-11), M-04 | servicio |
| RF-016 | M-10 | comando |
| RF-017 | M-03, M-04, M-07 | modelo + servicio |
| RF-018 | M-06, M-08 | modelo + panel |
| RF-019 | M-08 (D-09), M-11 | panel + migraciones |
| RF-020 | M-09, M-08 | historial + panel |

## RF sin cobertura
Ninguno.
