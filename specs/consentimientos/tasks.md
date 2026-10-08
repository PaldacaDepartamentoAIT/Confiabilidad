# Tareas: consentimientos
Estado: aprobado

Rutas relativas a `backend/apps/consents/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores. En cada
tarea, antes de marcarla, se prueba al menos un mutante del código que introduce y debe hacer
fallar sus tests. Mientras la feature no esté terminada, `migrations/0001_initial.py` se regenera
en cada tarea que cambia el esquema, para que al final queden solo las dos migraciones de M-11. Tras el cambio H-1, la tercera
(`0003`, D-17) es una migración nueva, porque la rama ya se ha migrado en bases de desarrollo.

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

- [x] T-018 Grupo «Soporte técnico»
  RF: RF-019 | Depende de: T-017 | Archivos: 2
  Archivos: `migrations/0002_support_group.py`, `tests/test_migrations.py`.
  Hecho cuando: tras migrar desde cero existe el grupo con los permisos de ver, crear, editar y
  borrar `UserTerms` y `MarketingConsent`, y ninguno de `Terms`; deshacer la migración lo borra;
  suite verde. (CF-1)
  Decisiones: mutante equivalente — quitar el filtro `app_label=consents` no cambia nada, porque ningún otro modelo se llama `userterms` ni `marketingconsent` — [Cierto]. El nombre del grupo se guarda en español («Soporte técnico») porque es un dato visible en el panel, no un texto del código — [Probable] — revertir: renombrarlo en una migración.

- [x] T-019 Panel de documentos
  RF: RF-004, RF-005 | Depende de: T-018 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin_terms.py`.
  Hecho cuando: un staff con permisos de `Terms` crea, edita y borra documentos desde el panel y
  ve si tienen aceptaciones; un staff sin permisos recibe 403; en una versión aceptada los campos
  protegidos salen de solo lectura, el borrado individual no está disponible y el borrado masivo
  no borra ninguno de sus documentos; suite verde. (CF-2)
  Decisiones: la acción de borrado masivo de Django ya consulta `has_delete_permission` por objeto; si la selección incluye un documento de una versión aceptada, rechaza toda la acción (403) y no borra nada, ni siquiera los libres. `delete_queryset` borra igualmente uno a uno y omite los bloqueados (D-04), como defensa si se llama por otra vía — [Cierto] — revertir: quitar el bloqueo de `has_delete_permission` para que la acción borre los libres y omita los bloqueados.

- [x] T-020 Panel de soporte técnico
  RF: RF-019, RF-010, RF-018, RF-012 | Depende de: T-019 | Archivos: 2
  Archivos: `admin.py`, `tests/test_admin_support.py`.
  Hecho cuando: un miembro de «Soporte técnico» ve, crea, edita y borra aceptaciones y
  consentimientos, incluidos documentos no vigentes y cuentas inactivas; la acción «Revocar»
  revoca las filas seleccionadas; la huella sale de solo lectura y se calcula sola; un staff con
  los mismos permisos de modelo pero fuera del grupo recibe 403; un superusuario puede; suite verde.
  (CF-3)
  Decisiones: el acceso exige ser staff activo, además de pertenecer al grupo o ser superusuario — [Cierto]. Al crear, el formulario exige usuario para que el error salga en el formulario y no como un 500; al editar se puede vaciar (la huella se conserva, T-011) — [Probable] — revertir: `required = True` siempre. El usuario se elige por id (`raw_id_fields`) para no cargar todos los usuarios en un desplegable — [Cierto]. La acción «Revocar» ignora las filas ya revocadas — [Cierto].

- [x] T-021 Historial en el panel, con autor y sin revertir
  RF: RF-020 | Depende de: T-020 | Archivos: 3
  Archivos: `admin.py`, `backend/config/settings.py`, `tests/test_admin_history.py`.
  Hecho cuando: un cambio hecho desde el panel queda en el historial con el usuario que lo hizo;
  la vista de historial de las tres tablas se abre; la vista de revertir a una versión anterior no
  está disponible (`SIMPLE_HISTORY_REVERT_DISABLED`); suite verde. (CF-3)
  Decisiones: `SIMPLE_HISTORY_REVERT_DISABLED` solo oculta el botón, y la vista de una versión antigua seguía aceptando POST y guardando. Se añadió `_HistoryAdmin`, que responde 403 a cualquier POST de esa vista en las tres tablas — [Cierto] — revertir: quitar `_HistoryAdmin.history_form_view`. El ajuste es global y afecta también a otros modelos con historial (hoy `User`, que no está en el panel) — [Cierto].

- [x] T-022 Comando: documento vigente y aceptar términos
  RF: RF-016 | Depende de: T-016 | Archivos: 4
  Archivos: `management/__init__.py`, `management/commands/__init__.py`,
  `management/commands/consents.py`, `tests/test_consents_command.py`.
  Hecho cuando: `manage.py consents current --kind terms --locale es` muestra versión, idioma y
  contenido del vigente, o un error si no hay; `accept-terms <correo> --version V --locale es`
  registra la aceptación y muestra el error de D-12 si se rechaza o si el correo no existe; suite
  verde.
  Excepción: dos de los archivos son los paquetes vacíos que Django exige para descubrir comandos.
  Decisiones: el usuario se busca por correo sin distinguir mayúsculas — [Cierto]. Los errores del servicio se muestran con su mensaje en inglés, como en `registration` — [Cierto]. Mutante equivalente: mostrar el idioma pedido en lugar del del documento no cambia la salida, porque coinciden siempre — [Cierto].

- [x] T-023 Comando: conceder, revocar y estado
  RF: RF-016 | Depende de: T-022 | Archivos: 2
  Archivos: `management/commands/consents.py`, `tests/test_consents_command.py`.
  Hecho cuando: `grant-marketing <correo> --version V --locale es`, `revoke-marketing <correo>` y
  `status <correo>` llaman al servicio y muestran el resultado o el error; suite verde. (CF-5)
  Decisiones: `revoke-marketing` sin consentimiento activo muestra `revoked: none` y termina sin error, igual que el servicio (RF-010) — [Cierto]. Mutante equivalente: la comprobación `revoked_at is None` existe solo para el tipado, porque una fila revocada siempre tiene fecha — [Cierto].

- [x] T-024 Resumen de la feature
  RF: — (AGENTS.md) | Depende de: T-021, T-023 | Archivos: 1
  Archivos: `specs/consentimientos/resumen.md`.
  Hecho cuando: el resumen explica qué se hizo, cómo probarlo paso a paso (panel y comando) y un
  marco teórico de los conceptos que generaron dudas (huella HMAC, versión en vigor, exigencia de
  nueva aceptación, `SET_NULL`). (CF-5)
  Decisiones: además se anota en `HUMAN_TODO.md` la migración y la comprobación de Docker, porque la imagen no se pudo construir aquí (429 de Docker Hub) — [Cierto].

- [x] T-025 Corrección: rechazar etiquetas HTML con «/» como separador de atributos
  Tipo: corrección | Origen: validación de RF-001
  RF: RF-001 | Depende de: — | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Causa: `_HTML_PATTERN` solo reconoce espacios tras el nombre de la etiqueta, así que
  `<svg/onload=…>`, `<img/src=x/onerror=…>` o `<details/open/ontoggle=…>` se guardan.
  Hecho cuando: `test_content_with_html_is_rejected` incluye esos casos y pasa; los casos permitidos
  de D-08 siguen aceptándose; la suite completa sigue en verde.

- [x] T-026 Corrección: versionar en el historial el vaciado del usuario al borrar la cuenta — DESCARTADA
  Tipo: corrección | Origen: validación de RF-020
  RF: RF-020, RF-013 | Depende de: — | Archivos: 2 o 3
  Causa: `SET_NULL` se aplica con un `UPDATE` masivo que no deja versión ni autor en `UserTerms` ni
  en `MarketingConsent`; además, `test_history_survives_deleting_the_user` fijaba ese fallo.
  Hecho cuando: al borrar la cuenta queda en las dos tablas una versión `~` con el usuario vacío,
  la huella intacta y el estado sin cambios; RF-013 sigue cumpliéndose; la suite completa sigue en
  verde.
  Descartada: el cambio del 2026-10-08 (C-14) decide que el vaciado por borrado de la cuenta no
  genera versión; no se implementa. Su test lo reescribe T-029.

- [x] T-027 Corrección: huella inmutable y usuario no reasignable
  Tipo: corrección | Origen: cambio H-1 (2026-10-08)
  RF: RF-012, RF-019 | Depende de: — | Archivos: 2
  Archivos: `models.py`, `tests/test_acceptance_models.py`.
  Causa: T-011 recalculaba la huella al cambiar el usuario de una fila; RF-012 ahora lo prohíbe
  (D-16). Ajusta T-011 sin desmarcarla.
  Hecho cuando: en las dos tablas, asignar otro usuario a una fila existente lanza
  `ValidationError` en `user`, también si la fila no tenía usuario; vaciarlo se permite y conserva
  la huella; la huella guardada no cambia por ninguna vía; se retira
  `test_changing_the_user_of_a_record_recalculates_the_hash`; suite verde.
  Decisiones: guardar con el mismo usuario (otra instancia del mismo id) se permite, porque no es una reasignación — [Cierto]. El error usa el código `user_reassigned` — [Cierto].

- [x] T-028 Corrección: el panel muestra el error al reasignar el usuario
  Tipo: corrección | Origen: cambio H-1 (2026-10-08)
  RF: RF-012, RF-019 | Depende de: T-027 | Archivos: 1
  Archivos: `tests/test_admin_support.py`.
  Causa: comprobar que la regla de D-16 llega al formulario de soporte sin error 500.
  Hecho cuando: editar desde el panel una aceptación y un consentimiento con otro usuario responde
  200 con el error en `user` y no cambia la fila; editarlos con el usuario vacío responde 302 y
  conserva la huella; suite verde.
  Decisiones: estos tests pasaron a la primera, porque el comportamiento ya lo implementó T-027 (`clean()`, D-16). Que de verdad lo prueban se comprobó con un mutante de T-027 (sin la comparación de usuario), que los hace fallar — [Cierto].

- [x] T-029 Corrección: historial sin usuario y autor filtrado
  Tipo: corrección | Origen: cambio H-1 (2026-10-08)
  RF: RF-020 | Depende de: T-027 | Archivos: 3
  Archivos: `models.py`, `migrations/0003_history_without_user.py`, `tests/test_history.py`.
  Causa: T-017 guardaba el usuario en el historial y registraba como autor a cualquier usuario de
  la petición (D-15, D-17). Ajusta T-017 sin desmarcarla.
  Hecho cuando: `migrate` aplica `0003` sobre una base con `0002`; los históricos de
  `UserTerms` y `MarketingConsent` no tienen `user`; borrar la cuenta no añade versión; con una
  petición del propio usuario de la fila o de alguien que no es staff, la versión queda sin autor,
  y con un staff distinto queda con él; suite verde.
  Excepción: también `tests/test_migrations.py`, porque su fixture volvía a `0002` y dejaba la base
  de tests sin `0003`; el test de que `0003` se aplica sobre `0002` vive ahí.
  Decisiones: el panel fija `_history_user` directamente (`SimpleHistoryAdmin.save_model`) y se saltaba `get_user`; `save()` filtra también ese autor explícito — [Cierto] — revertir: quitar `_filter_explicit_author`. Un staff inactivo no consta como autor — [Probable] — revertir: no exigir `is_active` en `_allowed_author`. El autor de un borrado también se filtra, pero solo por la vía de la petición; el autor explícito al borrar lo corrige T-034 — [Cierto].

- [x] T-030 Actualizar el resumen tras el cambio H-1
  RF: — (AGENTS.md) | Depende de: T-028, T-029 | Archivos: 1
  Archivos: `specs/consentimientos/resumen.md`.
  Hecho cuando: el resumen refleja la huella inmutable, el usuario no reasignable, el historial sin
  usuario y el autor filtrado; los límites conocidos y el marco teórico (seudonimización, «dato
  directo») están al día, y se quita el límite del vaciado sin versión, que ahora es el
  comportamiento pedido.

- [x] T-031 Corrección: no registrar como autor al usuario que vacía su propia fila
  Tipo: corrección | Origen: validación de RF-020
  RF: RF-020 | Depende de: — | Archivos: 2
  Archivos: `models.py`, `tests/test_history.py`.
  Causa: `_allowed_author` compara con el `user_id` nuevo; al vaciar el usuario, el dueño (si es
  staff activo) queda como autor, tanto por `_history_user` (panel) como por `get_user`.
  Hecho cuando: en las dos tablas, si un staff vacía el usuario de su propia fila (también desde
  el panel), la versión `~` queda sin autor; si lo vacía otro staff, queda con él; en filas
  existentes se compara también con el `user_id` guardado; la suite completa sigue en verde.
  Decisiones: `save()` recuerda el `user_id` guardado antes de escribir (`_stored_user_id`), porque el autor se resuelve después del guardado, cuando la fila ya está vacía; el filtro excluye tanto al usuario nuevo como al guardado — [Cierto] — revertir: quitar `_remember_stored_user`.

- [x] T-032 Corrección: el test de desempate de la versión vigente distingue el orden de creación del alfabético
  Tipo: corrección | Origen: validación de RF-003
  RF: RF-003 | Depende de: — | Archivos: 1
  Archivos: `tests/test_versions.py`.
  Causa: el escenario crea "b" antes que "a", así que un orden alfabético también lo pasa.
  Hecho cuando: el test cubre también el caso en que la versión creada más tarde va después
  alfabéticamente ("a" y luego "b"; se espera "b"); un mutante que ordena por la etiqueta lo hace
  fallar; la suite sigue en verde.
  Decisiones: el test nuevo pasó a la primera, porque el código ya era correcto (lo confirmó la validación); que mata el orden por etiqueta se comprobó con dos mutantes (`key` y `-key`) — [Cierto].

- [x] T-033 Corrección: rechazar cualquier etiqueta HTML salvo los enlaces automáticos de Markdown
  Tipo: corrección | Origen: validación de RF-001 (3.ª ronda)
  RF: RF-001 | Depende de: — | Archivos: 2
  Archivos: `validators.py`, `tests/test_validators.py`.
  Causa: `_HTML_PATTERN` enumera nombres de etiqueta `[A-Za-z][A-Za-z0-9-]*`, pero HTML acepta
  cualquier carácter salvo espacio, `/` o `>`; `<x_y onmouseover=…>`, `<x_y autofocus onfocus=…>`
  y `<a:b onclick=…>` se guardan, también desde el panel. Enumerar lo prohibido deja huecos.
  Hecho cuando: el validador rechaza todo `<` seguido de una letra, `/`, `!` o `?` que no forme un
  enlace automático de Markdown (`<esquema:…>` sin espacios ni `<>`, o `<correo@dominio>`);
  `test_content_with_html_is_rejected` incluye `<x_y onmouseover=…>`, `<x_y autofocus onfocus=…>`,
  `<a:b onclick=…>`, `<scr\x00ipt>` y `<![CDATA[x]]>`; siguen aceptándose `<https://x.com>`,
  `<mailto:legal@x.com>`, `<legal@x.com>`, `a < b and c > d`, `1 <2 and 3> 0` y `Use the <- arrow`;
  la suite completa sigue en verde.
  Decisión a registrar: `a<b` sin espacios se rechaza (falso positivo aceptado a cambio de no
  dejar huecos).
  Decisiones: `a<b` sin espacios se rechaza (falso positivo aceptado a cambio de no dejar huecos) — [Cierto]. Los enlaces automáticos siguen la definición de CommonMark: esquema de 2 a 32 caracteres sin espacios ni `<>`, o un correo; `<a:b>` (esquema de 1 carácter) cuenta como etiqueta y se rechaza — [Cierto] — revertir: ampliar `_AUTOLINK`. No se filtran esquemas peligrosos como `<javascript:…>`: no son HTML y RF-001 no los cubre; quien muestre el contenido debe sanear las URL — [Probable].

- [x] T-034 Corrección: filtrar también el autor explícito al borrar aceptaciones y consentimientos
  Tipo: corrección | Origen: validación de RF-020 (4.ª ronda)
  RF: RF-020 | Depende de: — | Archivos: 2
  Archivos: `models.py`, `tests/test_history.py`.
  Causa: `_filter_explicit_author` solo se aplica en `save()`; en `delete()`, `get_history_user`
  devuelve `_history_user` tal cual y deja como autor al dueño de la fila o a alguien que no es
  staff. La decisión de T-029 «el autor de un borrado también se filtra» solo era cierta por la vía
  de la petición.
  Hecho cuando: en las dos tablas, `delete()` con `_history_user` igual al usuario de la fila, o a
  un usuario que no es staff activo, deja la versión `-` sin autor; con otro staff activo queda con
  él; un mutante que quite el filtro en `delete()` hace fallar el test; la suite completa sigue en
  verde.
  Decisiones: `delete()` de las dos tablas filtra `_history_user` antes de borrar; el borrado masivo (`QuerySet.delete`) no lo necesita, porque carga cada fila sin autor explícito y pasa por `get_user` — [Cierto] — revertir: quitar los `delete()` añadidos.

- [x] T-035 Corrección: el listado del panel muestra qué documentos tienen aceptaciones
  Tipo: corrección | Origen: validación de RF-004 (5.ª ronda)
  RF: RF-004 | Depende de: — | Archivos: 1
  Archivos: `tests/test_admin_terms.py`.
  Causa: el test solo llama a `has_acceptances_display()`; quitar la columna de `list_display` no
  lo hace fallar.
  Hecho cuando: el test comprueba en la respuesta del listado la columna «Has acceptances» con el
  valor correcto en un documento de una versión aceptada y en uno de una versión libre; el mutante
  que quita la columna de `list_display` lo hace fallar; la suite completa sigue en verde.
  Decisiones: el test lee la celda `field-has_acceptances_display` de cada fila renderizada con `results()` del listado, así que falla si se quita la columna o si cambia su valor; mató dos mutantes (quitar la columna y devolver siempre False) — [Cierto].

- [x] T-036 Corrección: filtrar en el borrado también al usuario guardado de la fila
  Tipo: corrección | Origen: validación de RF-020 (5.ª ronda)
  RF: RF-020 | Depende de: — | Archivos: 2
  Archivos: `models.py`, `tests/test_history.py`.
  Causa: `delete()` de `UserTerms` y `MarketingConsent` no recuerda el `user_id` guardado; si la
  fila se vacía en memoria antes de borrarla, su dueño consta como autor de la versión `-`, tanto
  por la petición como por `_history_user`.
  Hecho cuando: en las dos tablas, si el dueño (staff activo) vacía el usuario en memoria y borra
  la fila, por la petición o con `_history_user`, la versión `-` queda sin autor; si borra otro
  staff activo, queda con él; el mutante que quita esa comprobación en `delete()` hace fallar el
  test; además se revisan todas las vías de autor (guardar y borrar, por petición y explícito, en
  las dos tablas) y cualquier hueco equivalente se anota; la suite completa sigue en verde.
  Decisiones: `delete()` recuerda el `user_id` guardado antes de borrar, igual que `save()` — [Cierto]. Revisión de las vías de autor (sondas fuera del repo): guardar y borrar, por la petición y con `_history_user`, en las dos tablas; y desde el panel, borrar, borrar en bloque, «Revoke selected» y vaciar el usuario en el formulario hechos por el propio dueño, más una instancia desfasada que se borra después de que otra vaciara el usuario. En todos los casos la versión queda sin autor; no se encontró ningún hueco equivalente — [Cierto]. Las escrituras masivas (`QuerySet.update`, `bulk_create`) no generan historial, así que no tienen autor que filtrar — [Cierto].

## RF sin tarea
Ninguno.
