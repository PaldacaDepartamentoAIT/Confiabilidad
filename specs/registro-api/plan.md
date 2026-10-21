# Plan: registro-api
Estado: aprobado

Base de código: el `main` con `correo-asincrono-plantillas` fusionada (S-17, CF-6). Las rutas y
funciones de `apps/accounts/registration.py`, `PhantomProcess`, `apps/emails/locales.py` y
`apps/core/fingerprints.py` citadas aquí son las de esa feature.

## Dependencias previas a implementar
- `sdd-cambio` en `procesos-pendientes` (S-03, CF-6): el registro pendiente guarda el documento de
  términos aceptado y completar el registro registra su aceptación (M-07). Es el único cambio en
  otra feature: el resto usa funciones públicas existentes o reorganiza código sin cambiar su
  comportamiento.

## Módulos
### M-01 Vistas y rutas de la API (`apps/accounts/api/views.py`, `apps/accounts/api/urls.py`, `config/urls.py`)
Responsabilidad: `POST /api/browser/v1/registration` (cliente web, con CSRF) y
`POST /api/app/v1/registration` (cliente de aplicación, sin CSRF), las dos con la misma vista (D-01,
D-02). La vista, sin autenticación y sin mirar la sesión (S-14), hace en este orden (D-12): límite
por IP (M-06) → validación (M-02) → límite por correo e IP (M-06) → `registration.start` (M-07) →
respuesta. Respuestas (D-03, D-04):
- `202` `{"public_id": "<PUBLIC_ID>", "message": "<mensaje neutro>"}`;
- `400` `{"errors": {"<campo>": [{"code": "<código>", "message": "<texto>"}]}}`;
- `429` `{"message": "<texto>", "retry_after": <segundos>}` y cabecera `Retry-After`;
- `403` de Django si falta el CSRF en la variante web.
RF: RF-001, RF-005, RF-006, RF-007, RF-008, RF-010, RF-011, RF-014

### M-02 Validación del formulario (`apps/accounts/api/serializers.py`)
Responsabilidad: serializador con `name`, `birthdate` (ISO `AAAA-MM-DD`), `email`, `country`,
`terms` (`{"version", "locale", "accepted"}`) y `language` (opcional). Valida todos los campos y
devuelve todos los errores de cada uno (D-13): nombre, fecha y país con los validadores de la
cuenta (M-03); correo con el validador de M-03; términos con la marca `accepted` y
`consents.services.current_document_shown` (M-07). Los errores del propio serializador (campo
ausente, nulo, vacío o de tipo incorrecto) salen con su código de DRF (`required`, `null`,
`blank`, `invalid`). No consulta cuentas ni registros pendientes (RF-024 de `procesos-pendientes`).
RF: RF-002, RF-003, RF-004

### M-03 Validadores (`apps/accounts/validators.py`)
Responsabilidad: `validate_registration_email`, que exige el formato del validador de correo de
Django, un dominio con al menos un punto y que no sea una dirección IP, con o sin corchetes
(`ana@[192.0.2.1]`, `ana@192.0.2.1`, `ana@[IPv6:2001:db8::1]`) (D-14); y que
`validate_name` lance todos los errores que se cumplan a la vez, no solo el primero (D-13). El
modelo sigue rechazando igual: solo cambia cuántos errores informa.
RF: RF-002, RF-003

### M-04 Catálogo de textos por idioma (`apps/accounts/api/messages.py`)
Responsabilidad: un diccionario código → texto en `es`, `pt-BR` y `en` para cada error de campo
(los de M-02 y M-03, los de `usuario-personalizado` y los de `current_document_shown`), el mensaje
neutro (S-13) y el texto del límite superado, con sus parámetros (`%(max)d`, `%(years)d`…) (D-05).
Un código sin texto en algún idioma hace fallar la suite (CF-7).
RF: RF-002, RF-005, RF-013

### M-05 Idioma de la solicitud (`apps/accounts/api/language.py`)
Responsabilidad: `request_language(field, accept_language)`: el campo, si es uno de los tres de
`locales.SUPPORTED` con sus variantes de escritura; si no, `Accept-Language` por idioma base y en su
orden de preferencia (`es-*` → `es`, `pt-*` → `pt-BR`, `en-*` → `en`); si no, `locales.DEFAULT`
(D-06). El resultado elige los textos de M-04 y se pasa a `registration.start`.
RF: RF-013

### M-06 Límite de frecuencia (`apps/accounts/throttling.py`, `apps/accounts/conf.py`)
Responsabilidad: `check_ip(ip)` y `check_email_ip(email, ip)`. Cada una devuelve «permitido» y
apunta la solicitud, o «superado» con los segundos de espera sin apuntar nada (RF-010, S-06). Usa un
registro deslizante de marcas de tiempo en la caché de Redis (D-07), con claves formadas por la
huella del correo que ya calcula `consent_email_fingerprint` y la IP (D-08):
- correo e IP: como mucho 1 solicitud en `REGISTRATION_RATE_EMAIL_IP_INTERVAL_SECONDS` (60) y
  `REGISTRATION_RATE_EMAIL_IP_PER_HOUR` (5) en la última hora;
- IP: `REGISTRATION_RATE_IP_PER_HOUR` (20) en la última hora.
La espera es lo que falta para que la marca más antigua que bloquea salga de su ventana. La hora
actual se inyecta para los tests.
RF: RF-010, RF-011, RF-012

### M-07 Términos en el registro (`apps/accounts/models.py`, `apps/accounts/registration.py`, migración `0012`, `apps/consents/services.py`)
Responsabilidad, sujeta al `sdd-cambio` de `procesos-pendientes`:
- `PendingRegistration` gana `terms_version` y `terms_locale`, vacíos en los registros anteriores
  (D-10);
- `start` recibe la versión y el idioma del documento y los guarda en el `payload` de la plaza;
  `resolve_registration` los copia al crear un registro nuevo, y en un registro repetido conserva los
  del existente (RF-007, S-11);
- `complete` acepta el documento guardado con `consents.services.accept_terms` dentro de un punto
  de guardado de la misma transacción. Si no hay documento guardado o ya no es de la versión
  vigente, crea la cuenta sin aceptación (D-11, S-12);
- en `consents/services.py`, `_current_document_shown` pasa a ser pública
  (`current_document_shown`) para que M-02 la use sin duplicar la regla.
RF: RF-004, RF-006, RF-007, RF-009

### M-08 Configuración y documentación (`config/settings.py`, `backend/.env.example`, `resumen.md`, `HUMAN_TODO.md`)
Responsabilidad: los tres límites en `settings.py` y `.env.example`; `resumen.md` con las llamadas
`curl` de cada caso, de los dos clientes, de los errores y de los límites (CF-5); y en el
`HUMAN_TODO.md` de `cambio-contrasena`, marcar que el límite de frecuencia del formulario de registro
ya existe y que los del reenvío, la verificación y el restablecimiento siguen pendientes (S-15).
RF: RF-012 (CF-5)

## Modelo de datos
- `accounts.PendingRegistration`: `terms_version` CharField(20, blank) y `terms_locale`
  CharField(5, blank), con valor por defecto `""` (migración `0012`, sin tocar los datos existentes;
  C-13).
- `accounts.PhantomProcess.payload` (JSON, sin migración): añade `terms_version` y `terms_locale`.
- Caché `default` (Redis), sin tablas:
  - `registration-rate:email-ip:<huella del correo>:<IP>` → lista de marcas de tiempo, caduca a
    la hora;
  - `registration-rate:ip:<IP>` → ídem.
- Sin cambios en `consents` salvo la función pública de M-07.

## Decisiones
### D-01 Dos rutas, una por cliente
Elegida: `/api/browser/v1/registration` y `/api/app/v1/registration`, como `allauth.headless`
(`_allauth/browser/v1`, `_allauth/app/v1`).
Descartada: una sola ruta que decide el cliente por una cabecera.
Motivo: la protección CSRF se decide por ruta y no por un dato que envía el cliente, y los clientes
ya conocen ese reparto por el inicio de sesión.

### D-02 Vista de DRF sin autenticación y `csrf_protect` explícito en la variante web
Elegida: `APIView` con `authentication_classes = []`, `AllowAny` y, en la ruta web, la vista envuelta
en `csrf_protect`.
Descartada: `SessionAuthentication` de DRF.
Motivo: DRF marca sus vistas como exentas de CSRF y solo lo exige a una sesión iniciada; una
solicitud anónima pasaría sin CSRF (RF-014). Sin autenticación, además, la sesión no influye en nada
(S-14).

### D-03 `202 Accepted`
Elegida: `202` en los tres casos.
Descartada: `201 Created`.
Motivo: en la respuesta no se crea necesariamente ningún registro (RF-024 y RF-025 de
`procesos-pendientes`); `201` prometería un recurso que, con un correo con cuenta, no existe.

### D-04 Errores como lista de `{code, message}` por campo
Elegida: `{"errors": {"<campo>": [{"code", "message"}]}}`.
Descartada: el formato por defecto de DRF (`{"<campo>": ["<texto>"]}`).
Motivo: RF-002 y RF-013 piden un código estable en todos los idiomas además del texto; el formato de
DRF solo da el texto.

### D-05 Textos por idioma en un diccionario del código
Elegida: catálogo en `messages.py` indexado por el código del error, como D-08 de
`correo-asincrono-plantillas`. Los validadores siguen lanzando sus mensajes en inglés con
`gettext_lazy` (`AGENTS.md`); la API sustituye el texto por el del catálogo.
Descartada: catálogos `gettext` (`.po`/`.mo`).
Motivo: compilar `.mo` exige `msgfmt` (GNU gettext), que no está ni en la imagen de Docker ni en el
entorno de desarrollo: sería una dependencia nueva. El diccionario se prueba idioma a idioma.

### D-06 Idioma resuelto por la vista, no por `LocaleMiddleware`
Elegida: función propia (M-05) que usa `parse_accept_lang_header` de Django para leer la cabecera.
Descartada: activar `LocaleMiddleware`.
Motivo: el middleware cambiaría el idioma de todo el sitio (panel incluido), no conoce el campo del
formulario y no convierte `pt-PT` en `pt-BR` (S-20).

### D-07 Registro deslizante en la caché de Redis
Elegida: lista de marcas de tiempo por clave en la caché `default`, con caducidad de una hora.
Descartada: los throttles de DRF, y una tabla en la base de datos.
Motivo: los throttles de DRF se aplican antes de validar y no pueden contar solo las solicitudes
válidas (S-06) ni combinar dos ventanas en una clave; una tabla daría exactitud transaccional a
costa de una migración y una purga para datos que solo viven una hora. Si se vacía la caché, los
límites se reinician: es aceptable para un freno.

### D-08 Claves del límite con la huella del correo existente e IP en claro
Elegida: la huella del correo de `consent_email_fingerprint` (punto único de
`huellas-hmac-unificadas`, ya pública) y la IP tal cual.
Descartada: un tipo de huella propio del límite (exige un `sdd-cambio` en `huellas-hmac-unificadas`)
y el correo en claro en la clave de Redis.
Motivo: el correo no queda legible fuera de la base de datos y no se calcula ningún hash fuera del
punto único (RF-010 de esa feature), sin tocar otra spec. *Coste:* la IP queda en claro en Redis una
hora como mucho (ya consta en los registros del proxy), y la clave del límite coincide con la huella
que guardan las aceptaciones de términos; las dos son internas del servidor.

### D-09 Carreras entre solicitudes simultáneas aceptadas
Elegida: leer, comprobar y escribir la lista sin bloqueo.
Descartada: un cerrojo en la caché alrededor de cada comprobación.
Motivo: solo solicitudes que llegan a la vez con la misma clave pueden colarse, y como mucho una por
solicitud simultánea. El cerrojo añade esperas y un modo de fallo (cerrojo huérfano) a todas las
solicitudes para evitar un exceso pequeño. *Riesgo aceptado:* un cliente que dispara muchas
solicitudes a la vez puede superar el límite por unas pocas.

### D-10 Documento guardado como versión e idioma
Elegida: dos campos de texto en `PendingRegistration`, los mismos datos que recibe `accept_terms`.
Descartada: una clave foránea a `consents.Terms`.
Motivo: no crea una dependencia de migraciones de `accounts` hacia `consents`, y un documento borrado
por el panel no bloquea ni rompe el registro: al completar, simplemente no es vigente (D-11).

### D-11 Aceptación en un punto de guardado al completar
Elegida: `accept_terms` dentro de un `atomic()` anidado; si rechaza el documento (ya no vigente o
inexistente), se crea la cuenta sin aceptación.
Descartada: comprobar antes si es vigente y llamar después.
Motivo: la regla de vigencia vive en `consents` (RF-006); repetirla aquí podría divergir, y entre la
comprobación y la llamada puede entrar en vigor otra versión.

### D-12 Orden: CSRF → límite por IP → validación → límite por correo e IP → registro
Elegida: ese orden.
Descartada: validar antes del límite por IP.
Motivo: RF-011 rechaza sin validar; RF-010 solo cuenta las válidas, así que va después de validar.
Las solicitudes rechazadas por CSRF o por un límite no se apuntan (S-06).

### D-13 Todos los errores de cada campo
Elegida: el serializador ejecuta cada validador del campo y junta sus errores, y `validate_name`
lanza a la vez todos los que se cumplan.
Descartada: informar solo del primer error de cada campo.
Motivo: RF-002 pide todos los errores de cada campo; sin el cambio, un nombre con dos problemas
obliga a corregir y reenviar dos veces.

### D-14 Correo estricto solo en la API
Elegida: `validate_registration_email` en el serializador; el modelo sigue con el validador actual.
Un dominio que sea una dirección IP, con o sin corchetes, se rechaza con `email_ip_domain`
(ajuste tras la 1.ª validación, 2026-10-21).
Descartada: endurecer el validador del modelo.
Motivo: S-08 limita la regla a la API; cambiar el modelo afectaría a las cuentas de consola y del
panel, fuera del alcance.

## Estrategia de tests
- Unitarios (`pytest`, sin HTTP):
  - `validate_registration_email`: dominios con y sin punto, IP entre corchetes, `+etiqueta`,
    dominios no ASCII (RF-003);
  - `validate_name` con varios errores a la vez (RF-002);
  - `request_language`: campo válido, variantes, campo inválido con cabecera, idioma base,
    preferencias ordenadas y sin nada (RF-013);
  - catálogo: cada código usado por M-02, M-03, `usuario-personalizado` y
    `current_document_shown` tiene texto en los tres idiomas (CF-7);
  - throttling con hora inyectada: intervalo de 60 s, 5 por hora, 20 por IP, espera calculada,
    rechazadas no apuntadas y ventanas que se liberan (RF-010, RF-011); valores cambiados por
    `settings` (RF-012).
- Integración de la API (`APIClient`; `enforce_csrf_checks=True` en la ruta web):
  - solicitud válida → `202` con `public_id` y mensaje; `start` llamado con idioma y documento
    (RF-001);
  - cada campo inválido con su código, y varios campos a la vez (RF-002, CF-4); cada motivo de
    términos con su código (RF-004);
  - CF-2: correo nuevo, con registro pendiente, con cuenta activa y con cuenta inactiva dan el mismo
    código, cuerpo salvo `public_id`, cabeceras y cookies; lo mismo para el `429` (RF-005, RF-010);
  - ruta web sin CSRF → `403` sin apuntar ni empezar nada; ruta de aplicación sin CSRF ni `Origin`
    → `202` (RF-014);
  - textos en el idioma pedido (RF-013).
- Integración del registro (servicio, con la cola en modo síncrono o llamando a la tarea):
  - correo nuevo crea el registro con el documento y encola el código (RF-006);
  - correo con registro pendiente conserva sus datos y su documento (RF-007);
  - correo con cuenta: ningún registro pendiente con ese `public_id` (CF-3) y aviso encolado o no
    según esté activa (RF-008);
  - completar acepta el documento con la fecha de compleción; sin documento o con uno no vigente,
    cuenta sin aceptación; antes de completar, ninguna aceptación nueva (RF-009).
- Mutación (P-04, `AGENTS.md`): un mutante por tarea sobre la condición principal (orden de D-12,
  comparaciones de las ventanas, marca `accepted`).
- Verificación desde consola (P-03): las llamadas `curl` de `resumen.md` (CF-5).

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02, M-07 | integración API |
| RF-002 | M-02, M-03, M-04 | unitario, integración API |
| RF-003 | M-02, M-03 | unitario, integración API |
| RF-004 | M-02, M-07 | integración API |
| RF-005 | M-01, M-04 | integración API (CF-2) |
| RF-006 | M-01, M-07 | integración registro |
| RF-007 | M-01, M-07 | integración registro |
| RF-008 | M-01 | integración registro (CF-3) |
| RF-009 | M-07 | integración registro |
| RF-010 | M-06, M-01 | unitario, integración API |
| RF-011 | M-06, M-01 | unitario, integración API |
| RF-012 | M-06, M-08 | unitario |
| RF-013 | M-04, M-05 | unitario, integración API |
| RF-014 | M-01 | integración API |

## RF sin cobertura
Ninguno.
