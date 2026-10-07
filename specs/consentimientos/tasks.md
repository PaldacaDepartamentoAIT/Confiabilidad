# Tareas: consentimientos
Estado: aprobado

Rutas relativas a `backend/apps/consents/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea, antes de marcarla, se prueba al menos un mutante del código que introduce y debe hacer
fallar sus tests. Mientras la feature no esté terminada, `migrations/0001_initial.py` se regenera
en cada tarea que cambia el esquema, para que al final queden solo las dos migraciones de M-11.

- [x] T-001 Andamiaje de la app `consents`
  RF: — (M-01, D-01) | Depende de: — | Archivos: 4
  Archivos: `__init__.py`, `apps.py`, `tests/__init__.py`, `backend/config/settings.py`.
  Hecho cuando: `python manage.py check` no da errores y `apps.get_app_config("consents")` resuelve
  con `apps.consents` en `INSTALLED_APPS`; suite verde.
  Excepción: andamiaje; tres de los archivos son paquetes vacíos o casi vacíos y no se pueden
  separar sin dejar una app a medias.

- [x] T-002 Validadores de idioma, versión y contenido
  RF: RF-001 | Depende de: T-001 | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Hecho cuando: se aceptan `es`, `pt-BR` y `en` y se rechazan otros (`pt`, `es-ES`, `fr`); se
  aceptan versiones como `1`, `2.1` y `2026-10` y se rechazan vacías, de 21 caracteres o con
  espacios u otros símbolos; el contenido con `<p>`, `</a>`, `<!--` o `<!DOCTYPE` se rechaza y con
  `<https://x.com>` o `a < b` se acepta (D-08); suite verde.
  Decisiones: los códigos de idioma distinguen mayúsculas (`pt-br` y `EN` se rechazan) para que cada idioma tenga una sola forma guardada — [Probable] — revertir: normalizar a la forma canónica antes de validar. Un texto como `<b and c>` cuenta como etiqueta HTML y se rechaza — [Cierto] — revertir: exigir un nombre de etiqueta HTML conocido.

- [x] T-003 Secreto de la huella del correo
  RF: RF-012 | Depende de: T-001 | Archivos: 3
  Archivos: `conf.py`, `backend/config/settings.py`, `tests/test_conf.py`.
  Hecho cuando: sin variable de entorno, `conf.email_hash_secret()` vale `SECRET_KEY`; con
  `override_settings` devuelve el valor cambiado; vacío o solo espacios lanza
  `ImproperlyConfigured`; suite verde.

- [x] T-004 Huella del correo
  RF: RF-012 | Depende de: T-003 | Archivos: 2
  Archivos: `hashing.py`, `tests/test_hashing.py`.
  Hecho cuando: la huella tiene 64 caracteres hexadecimales y no contiene el correo; `" Ana@X.com "`
  y `"ana@x.com"` dan la misma; correos distintos dan huellas distintas; otro secreto da otra
  huella; coincide con un HMAC-SHA256 calculado aparte; suite verde.

- [x] T-005 Documentar el secreto de la huella
  RF: RF-012 (documentación) | Depende de: T-003 | Archivos: 2
  Archivos: `backend/.env.example`, `HUMAN_TODO.md`.
  Hecho cuando: `.env.example` lista `CONSENT_EMAIL_HASH_SECRET` sin valor real y `HUMAN_TODO.md`
  pide definirlo cifrado con SOPS en producción, con el aviso de no rotarlo nunca (S-09, D-06).

- [x] T-006 Modelo `Terms` con su unicidad de versión
  RF: RF-001, RF-002 | Depende de: T-002 | Archivos: 3
  Archivos: `models.py`, `migrations/0001_initial.py`, `tests/test_terms_model.py`.
  Hecho cuando: `migrate` aplica `0001`; se guardan todos los campos de RF-001 con `created_at`
  automático y `published_at` opcional; un idioma, versión o contenido inválido lanza
  `ValidationError` al guardar; "V1" y "v1" del mismo tipo e idioma chocan, también por
  `bulk_create` (`IntegrityError`), y no chocan en otro idioma u otro tipo; suite verde. (CF-1)
  Excepción: además se crea `migrations/__init__.py`, paquete vacío que Django exige y que faltó en el andamiaje de T-001.
  Decisiones: `save()` llama a `full_clean()` con validación de restricciones, así que un duplicado da `ValidationError` en guardados normales y `IntegrityError` solo en cargas masivas — [Cierto] — revertir: `full_clean(validate_constraints=False)`.

- [x] T-007 Exigencia de nueva aceptación
  RF: RF-017, RF-001 | Depende de: T-006 | Archivos: 2
  Archivos: `models.py`, `tests/test_terms_model.py`.
  Hecho cuando: un documento de términos se crea con `requires_reacceptance=True` por defecto; uno
  de marketing se guarda siempre con `False` (D-07); guardar un documento de términos con un valor
  distinto del de otro idioma de su versión lanza `ValidationError`; suite verde.
  Decisiones: mutante equivalente — quitar la condición `kind == terms` de la coherencia no cambia nada, porque `save()` deja siempre `False` en marketing — [Cierto]. La coherencia se compara con la versión sin distinguir mayúsculas, igual que la unicidad de RF-002 — [Cierto] — revertir: `version=` en `_siblings`.

- [x] T-008 Versión vigente
  RF: RF-003 | Depende de: T-007 | Archivos: 3
  Archivos: `versions.py`, `tests/factories.py`, `tests/test_versions.py`.
  Hecho cuando: una versión con los tres idiomas publicados está en vigor desde la fecha más
  tardía de los tres; si falta un idioma, alguno es borrador o tiene fecha futura, no lo está; con
  varias en vigor, la vigente es la más reciente y, a igual fecha, la creada más tarde; sin
  ninguna, no hay vigente; el documento vigente en un idioma es el de la versión vigente; las
  factorías `make_document` y `publish_version` crean documentos y versiones completas; suite verde.
  Decisiones: `InForceVersion.version` guarda la versión en minúsculas, porque es la clave común a los tres idiomas — [Cierto] — revertir: devolver la etiqueta del documento más reciente. Mutante equivalente: `published_at__lte` → `__lt` solo difiere si la publicación coincide al microsegundo con la consulta — [Cierto].

- [x] T-009 Modelo `UserTerms`
  RF: RF-007, RF-013, RF-018 | Depende de: T-008 | Archivos: 3
  Archivos: `models.py`, `migrations/0001_initial.py`, `tests/test_acceptance_models.py`.
  Hecho cuando: `migrate` aplica `0001` regenerada; se guardan usuario, documento, huella, fecha de
  aceptación y fecha de revocación opcional; un documento de marketing se rechaza; dos aceptaciones
  no revocadas del mismo usuario y documento chocan, también por `bulk_create`, y una revocada no
  choca; borrar el usuario deja la fila con usuario vacío; borrar el documento aceptado lanza
  `ProtectedError`; suite verde.
  Decisiones: el tipo de documento se valida con `limit_choices_to` de la FK, que Django comprueba en `full_clean`; una comprobación propia era un mutante equivalente y se quitó — [Cierto] — revertir: añadir un `clean()` con la comprobación de `kind`.

- [x] T-010 Modelo `MarketingConsent`
  RF: RF-010, RF-011, RF-013 | Depende de: T-009 | Archivos: 3
  Archivos: `models.py`, `migrations/0001_initial.py`, `tests/test_acceptance_models.py`.
  Hecho cuando: `migrate` aplica `0001` regenerada; se guardan usuario, documento, huella,
  `granted`, fecha de concesión y fecha de revocación opcional; un documento de términos se
  rechaza; dos consentimientos activos del mismo usuario chocan, también por `bulk_create`; dos
  activos sin usuario no chocan; `granted=True` con `revoked_at` o `granted=False` sin él chocan
  con el `CheckConstraint`; borrar el usuario deja el activo activo y sin usuario; suite verde.

- [x] T-011 Huella automática y usuario obligatorio
  RF: RF-012, RF-013 | Depende de: T-004, T-010 | Archivos: 2
  Archivos: `models.py`, `tests/test_acceptance_models.py`.
  Hecho cuando: en las dos tablas, al crear se guarda la huella del correo del usuario aunque se
  pase otra; cambiar el correo del usuario no cambia la huella guardada; cambiar el usuario de la
  fila la recalcula; crear una fila sin usuario lanza `ValidationError`; guardar una fila ya sin
  usuario (cuenta borrada) conserva su huella; suite verde.
  Decisiones: vaciar el usuario de una fila existente (soporte) conserva su huella, igual que al borrar la cuenta (RF-013) — [Probable] — revertir: rechazar el usuario vacío en filas existentes. Una huella escrita a mano en una fila existente se descarta y se restaura la guardada — [Cierto].

- [x] T-012 Versión aceptada inmutable en el modelo
  RF: RF-005 | Depende de: T-011 | Archivos: 2
  Archivos: `models.py`, `tests/test_terms_model.py`.
  Hecho cuando: si un documento de una versión tiene una aceptación o un consentimiento (revocado
  incluido), cambiar contenido, versión, idioma, tipo, fecha de publicación o
  `requires_reacceptance` de cualquier documento de esa versión lanza `ValidationError`, y
  `delete()` también; sin aceptaciones se puede editar y borrar; suite verde.
  Decisiones: el bloqueo se comprueba en `save()` antes de `full_clean()` y se lanza solo, para que el error no se mezcle con otros (p. ej., unicidad al cambiar el idioma); por eso el panel debe mostrar esos campos de solo lectura (T-019) — [Cierto] — revertir: moverlo a `clean()`. Guardar un documento aceptado sin cambios está permitido — [Cierto].

- [x] T-013 Aceptar términos
  RF: RF-006, RF-007, RF-014, RF-018 | Depende de: T-012 | Archivos: 2
  Archivos: `services.py`, `tests/test_services.py`.
  Hecho cuando: `accept_terms` registra la aceptación del documento vigente indicado por versión e
  idioma con su huella y fecha; rechaza con el `code` de D-12 un documento inexistente, de
  marketing, de una versión no vigente o una cuenta inactiva, sin registrar nada; repetirla
  devuelve la misma fila; tras revocarla, aceptar crea una nueva; un choque simultáneo con la
  unicidad devuelve la existente (D-10); suite verde.
  Decisiones: el servicio recibe el usuario, la versión y el idioma; si el documento existe solo como marketing responde `wrong_kind`, y si no existe, `document_not_found` — [Cierto]. Aceptar el mismo documento en otro idioma crea otra aceptación, porque RF-007 compara documentos, no versiones — [Probable] — revertir: buscar la existente por versión. Mutante equivalente: quitar la búsqueda previa de la existente no cambia el resultado, porque la unicidad la devuelve igualmente; se mantiene por D-10 — [Cierto].

- [x] T-014 Conceder marketing
  RF: RF-008, RF-009, RF-014 | Depende de: T-013 | Archivos: 2
  Archivos: `services.py`, `tests/test_services.py`.
  Hecho cuando: `grant_marketing` registra un consentimiento activo del documento vigente indicado;
  rechaza un documento inexistente, de términos, no vigente o una cuenta inactiva; con un activo
  del mismo documento devuelve el existente; con un activo de otro documento lo revoca y crea el
  nuevo en una sola transacción; suite verde.
  Decisiones: si al sustituir falla la creación del nuevo consentimiento, la revocación del anterior se deshace con la transacción y el usuario conserva el activo — [Cierto]. Conceder otro idioma de la misma versión cuenta como otro documento y sustituye al activo (RF-009 compara documentos) — [Probable] — revertir: comparar por versión.

- [x] T-015 Revocar marketing
  RF: RF-010, RF-014 | Depende de: T-014 | Archivos: 2
  Archivos: `services.py`, `tests/test_services.py`.
  Hecho cuando: `revoke_marketing` pone `granted=False` y la fecha de revocación en el activo y
  conserva la fila; sin activo no cambia nada ni falla; funciona con una cuenta inactiva; suite
  verde.
  Decisiones: `revoke_marketing` devuelve el consentimiento revocado, o `None` si no había activo, para que el comando y la futura API puedan informarlo — [Cierto].

- [x] T-016 Estado de consentimiento
  RF: RF-015, RF-017, RF-018 | Depende de: T-015 | Archivos: 3
  Archivos: `services.py`, `versions.py`, `tests/test_services.py`.
  Hecho cuando: `consent_status` indica "sin términos vigentes" si no hay versión en vigor; la
  primera versión exige aceptación; una versión nueva sin exigencia mantiene válida la aceptación
  anterior y una con exigencia la invalida; una aceptación en otro idioma de la versión vale; una
  revocada no cuenta; devuelve el consentimiento de marketing activo y su documento, o ninguno;
  suite verde.
  Decisiones: la exigencia de la versión se agrega con `BoolOr` de PostgreSQL (la base del proyecto); como RF-017 obliga a que coincida en los tres idiomas, `BoolAnd` daría lo mismo — [Cierto] — revertir: `Max` sobre un `Case`. No se filtra por tipo al contar aceptaciones: `UserTerms` solo admite documentos de términos, y el filtro era un mutante equivalente — [Cierto]. El estado devuelve `accepted`, `not_accepted` o `no_current_version` más el consentimiento de marketing activo — [Cierto].

- [x] T-017 Historial de las tres tablas
  RF: RF-020 | Depende de: T-016 | Archivos: 3
  Archivos: `models.py`, `migrations/0001_initial.py`, `tests/test_history.py`.
  Hecho cuando: `migrate` aplica `0001` regenerada con los históricos; alta, modificación y borrado
  de un documento, una aceptación y un consentimiento dejan cada uno una versión con todos sus
  datos y el tipo de cambio; el historial sigue tras el borrado; suite verde.
  Decisiones: al borrar la cuenta, el `SET_NULL` que vacía el usuario de aceptaciones y consentimientos lo hace Django con un `UPDATE` masivo, que no pasa por `save()`, así que no añade una versión al historial. El borrado de la cuenta sí queda en el historial del usuario, y la versión anterior conserva el id — [Cierto] — revertir: una señal `pre_delete` de `User` que guarde cada fila con el usuario vacío.

- [ ] T-018 Grupo «Soporte técnico»
  RF: RF-019 | Depende de: T-017 | Archivos: 2
  Archivos: `migrations/0002_support_group.py`, `tests/test_migrations.py`.
  Hecho cuando: tras migrar desde cero existe el grupo con los permisos de ver, crear, editar y
  borrar `UserTerms` y `MarketingConsent`, y ninguno de `Terms`; deshacer la migración lo borra;
  suite verde. (CF-1)

- [ ] T-019 Panel de documentos
  RF: RF-004, RF-005 | Depende de: T-018 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin_terms.py`.
  Hecho cuando: un staff con permisos de `Terms` crea, edita y borra documentos desde el panel y
  ve si tienen aceptaciones; un staff sin permisos recibe 403; en una versión aceptada los campos
  protegidos salen de solo lectura, el borrado individual no está disponible y el borrado masivo
  no borra ninguno de sus documentos; suite verde. (CF-2)

- [ ] T-020 Panel de soporte técnico
  RF: RF-019, RF-010, RF-018, RF-012 | Depende de: T-019 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin_support.py`.
  Hecho cuando: un miembro de «Soporte técnico» ve, crea, edita y borra aceptaciones y
  consentimientos, incluidos documentos no vigentes y cuentas inactivas; la acción «Revocar»
  revoca las filas seleccionadas; la huella sale de solo lectura y se calcula sola; un staff con
  los mismos permisos de modelo pero fuera del grupo recibe 403; un superusuario puede; suite verde.
  (CF-3)

- [ ] T-021 Historial en el panel, con autor y sin revertir
  RF: RF-020 | Depende de: T-020 | Archivos: 3
  Archivos: `admin.py`, `backend/config/settings.py`, `tests/test_admin_history.py`.
  Hecho cuando: un cambio hecho desde el panel queda en el historial con el usuario que lo hizo;
  la vista de historial de las tres tablas se abre; la vista de revertir a una versión anterior no
  está disponible (`SIMPLE_HISTORY_REVERT_DISABLED`); suite verde. (CF-3)

- [ ] T-022 Comando: documento vigente y aceptar términos
  RF: RF-016 | Depende de: T-016 | Archivos: 4
  Archivos: `management/__init__.py`, `management/commands/__init__.py`,
  `management/commands/consents.py`, `tests/test_consents_command.py`.
  Hecho cuando: `manage.py consents current --kind terms --locale es` muestra versión, idioma y
  contenido del vigente, o un error si no hay; `accept-terms <correo> --version V --locale es`
  registra la aceptación y muestra el error de D-12 si se rechaza o si el correo no existe; suite
  verde.
  Excepción: dos de los archivos son los paquetes vacíos que Django exige para descubrir comandos.

- [ ] T-023 Comando: conceder, revocar y estado
  RF: RF-016 | Depende de: T-022 | Archivos: 2
  Archivos: `management/commands/consents.py`, `tests/test_consents_command.py`.
  Hecho cuando: `grant-marketing <correo> --version V --locale es`, `revoke-marketing <correo>` y
  `status <correo>` llaman al servicio y muestran el resultado o el error; suite verde. (CF-5)

- [ ] T-024 Resumen de la feature
  RF: — (AGENTS.md) | Depende de: T-021, T-023 | Archivos: 1
  Archivos: `specs/consentimientos/resumen.md`.
  Hecho cuando: el resumen explica qué se hizo, cómo probarlo paso a paso (panel y comando) y un
  marco teórico de los conceptos que generaron dudas (huella HMAC, versión en vigor, exigencia de
  nueva aceptación, `SET_NULL`). (CF-5)

## RF sin tarea
Ninguno.
