# Tareas: huellas-hmac-unificadas
Estado: aprobado

Rutas relativas a `backend/apps/` salvo que se indique. "Suite verde" = `cd backend && pytest -q`
+ `mypy .` + `ruff check .` + `black --check .` sin errores. En cada tarea que cambia código de
producción, antes de marcarla, se prueba al menos un mutante de ese código y debe hacer fallar
sus tests, ejecutando el archivo de tests completo (nunca con `-k`). En las tareas que solo
mueven tests (T-005, T-006 y T-009), el mutante se aplica a `core/fingerprints.py` y debe hacer
fallar los tests movidos. Hasta T-007 y T-010 conviven el cálculo antiguo y el nuevo: es
intencionado, para que la suite no se rompa entre tareas, y T-012 lo prohíbe al final.

- [x] T-001 Huella del código con su clave y su política de rotación
  RF: RF-001, RF-002, RF-003, RF-005, RF-006, RF-007, RF-008 | Depende de: — | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Hecho cuando: `code_fingerprint(purpose, public_id, code)` coincide con dos vectores literales
  (registro y cambio de contraseña) generados con el `codes.code_fingerprint` actual antes de
  escribir el módulo nuevo (D-06), y con el HMAC calculado a mano; `code_matches` compara con la
  primitiva única en tiempo constante (espía: una llamada); acepta la clave anterior dentro del
  periodo de transición y la rechaza fuera de él; da los errores de RF-008 (clave vacía o anterior
  igual a la actual al calcular y comprobar; fecha de rotación inválida solo al comprobar; clave
  anterior sin fecha, ignorada); no hace ninguna consulta a la base de datos
  (`django_assert_num_queries(0)`); la clave por defecto sigue siendo `SECRET_KEY`; suite verde.
  Decisiones: (1) una fecha de rotación mal formada hace fallar toda comprobación, aunque la
  clave actual coincida y aunque no haya clave anterior, como dice el texto de RF-008; antes solo
  fallaba si la clave actual no coincidía. Lo decidió el usuario en una parada de esta tarea.
  [Cierto] Revertir: leer la clave anterior solo tras fallar la actual en `_matches`. (2) La
  política de cada clave es un `_KeyPolicy` con dos funciones (actual y anterior en transición),
  para que la huella de consentimientos (T-003) use la misma comparación sin clave anterior.
  [Probable] Revertir: dos funciones `_matches` separadas. (3) Un test comprueba que una clave
  anterior vacía nunca se usa como clave, para matar un mutante que aceptaría huellas firmadas con
  la clave vacía. [Cierto] Revertir: borrar
  `test_empty_previous_code_key_is_never_used_as_a_key`.

- [x] T-002 Sello de cuenta con la normalización única del correo
  RF: RF-004, RF-005, RF-006, RF-007 | Depende de: T-001 | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Hecho cuando: `account_stamp(email, password_hash)` coincide con un vector literal generado con
  el `codes.account_stamp` actual para un correo ya normalizado; `" Ana@X.com "` y `"ana@x.com"`
  dan el mismo sello (RF-004); `account_stamp_matches` compara en tiempo constante y acepta la
  clave anterior solo durante la transición; un sello nunca valida como huella de código; suite
  verde.

- [x] T-003 Huella del correo de consentimientos con su clave sin rotación
  RF: RF-002, RF-003, RF-004, RF-005, RF-006, RF-008 | Depende de: T-001 | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Hecho cuando: `consent_email_fingerprint(email)` coincide con un vector literal generado con el
  `email_fingerprint` actual de `consents/hashing.py`; normaliza el correo igual que el sello;
  `consent_email_matches` compara en tiempo constante y nunca usa una clave anterior, aunque
  existan los ajustes de rotación de la clave de códigos; una clave vacía da el error de RF-008;
  la clave sale de `CONSENT_EMAIL_HASH_SECRET`, con `SECRET_KEY` como valor por defecto (también
  leída del entorno en un subproceso, como hoy); sin consultas a la base de datos; suite verde.

- [x] T-004 Los procesos de registro y de cambio de contraseña usan el punto único
  RF: RF-001 | Depende de: T-002 | Archivos: 2
  Archivos: `accounts/processes.py`, `accounts/password_reset.py`.
  Hecho cuando: el comando siguiente no devuelve nada:
  `grep -nE "codes\.(code_fingerprint|verify_code|account_stamp)" backend/apps/accounts/processes.py backend/apps/accounts/password_reset.py`;
  las suites existentes de registro, cambio de contraseña y sus comandos pasan sin tocarlas (las
  huellas nuevas siguen verificando con las funciones antiguas porque el formato es idéntico,
  RF-005); suite verde.

- [x] T-005 Tests del registro y de los procesos contra el punto único
  RF: RF-001, RF-005 | Depende de: T-004 | Archivos: 3
  Archivos: `accounts/tests/test_processes.py`, `accounts/tests/test_registration_service.py`,
  `accounts/tests/test_registration_command.py`.
  Hecho cuando: esos tres archivos comprueban las huellas con `core.fingerprints` y ya no llaman
  a `codes.code_fingerprint` ni a `codes.verify_code`; conservan el mismo número de aserciones
  sobre huellas; un mutante en el mensaje de `code_fingerprint` hace fallar al menos uno de ellos;
  suite verde.
  Decisiones: un mutante que cambia el mensaje igual al calcular y al comprobar (por ejemplo,
  truncar el código) sobrevive en estos tests de integración, porque la ida y vuelta sigue siendo
  coherente; quitar el propósito del mensaje sí lo mata (`test_processes.py`), y los mutantes de
  formato los matan los vectores fijos de `core/tests/test_fingerprints.py` (D-06). [Cierto]
  Revertir: no aplica (es una limitación de los tests de integración, no un cambio de código).

- [x] T-006 Tests del cambio de contraseña contra el punto único
  RF: RF-001, RF-005 | Depende de: T-004 | Archivos: 2
  Archivos: `accounts/tests/test_password_reset_service.py`,
  `accounts/tests/test_password_reset_command.py`.
  Hecho cuando: esos dos archivos comprueban códigos y sellos con `core.fingerprints` y ya no
  llaman a `codes.verify_code` ni a `codes.account_stamp_matches`; conservan el mismo número de
  aserciones sobre huellas; un mutante en el mensaje de `account_stamp` hace fallar al menos uno
  de ellos; suite verde.

- [x] T-007 `codes.py` deja de firmar y comparar
  RF: RF-001 | Depende de: T-005, T-006 | Archivos: 2
  Archivos: `accounts/codes.py`, `accounts/tests/test_codes.py`.
  Hecho cuando: `codes.py` solo contiene `Purpose`, `generate_code` y `generate_public_id`, y no
  importa `hmac` ni `hashlib`; `test_codes.py` conserva solo los tests de esas tres piezas (los de
  huellas ya están en `core/tests/test_fingerprints.py` desde T-001 y T-002); suite verde.

- [x] T-008 `accounts/conf.py` deja de leer las claves de las huellas
  RF: RF-002 | Depende de: T-007 | Archivos: 2
  Archivos: `accounts/conf.py`, `accounts/tests/test_registration_conf.py`.
  Hecho cuando: `conf.py` ya no tiene `code_secret`, `previous_code_secret`, `secret_rotated_at`
  ni `secret_transition`; `test_registration_conf.py` deja de probarlos (sus casos están en
  `core/tests/test_fingerprints.py` desde T-001) y sigue probando el resto de límites, incluido
  `REGISTRATION_SECRET_TRANSITION_MINUTES` leído del entorno; suite verde.
  Decisiones: (1) `test_defaults` comprueba ahora que la transición por defecto es de 60 minutos
  leyendo el ajuste, porque al quitar `conf.secret_transition()` se perdía esa aserción exacta
  (los tests de `core` solo la acotan entre 30 y 61). [Cierto] Revertir: quitar esa línea.
  (2) Tarea de solo borrado: no introduce código en el que aplicar un mutante; la equivalencia la
  garantizan los tests de `core` (T-001) y la suite completa. [Cierto]

- [x] T-009 Tests de consentimientos contra el punto único
  RF: RF-001, RF-005 | Depende de: T-003 | Archivos: 3
  Archivos: `consents/tests/test_acceptance_models.py`, `consents/tests/test_admin_support.py`,
  `consents/tests/test_services.py`.
  Hecho cuando: esos tres archivos calculan la huella esperada con
  `core.fingerprints.consent_email_fingerprint` y ya no importan `consents.hashing`; un mutante que
  quite `strip()` en la normalización hace fallar al menos uno de ellos; suite verde.
  Decisiones: el mutante que quita `strip()` sobrevivía al principio, porque los correos de los
  tests ya están normalizados; añadí en `test_acceptance_models.py` un test que comprueba que la
  huella guardada coincide con la del correo escrito con espacios y mayúsculas (RF-004, y RF-012
  de `consentimientos`). [Cierto] Revertir: borrar
  `test_stored_hash_is_the_fingerprint_of_the_email_however_it_is_written`.

- [x] T-010 Los modelos de consentimientos usan el punto único y desaparece `hashing.py`
  RF: RF-001, RF-005 | Depende de: T-009 | Archivos: 3
  Archivos: `consents/models.py`, `consents/hashing.py` (se borra),
  `consents/tests/test_hashing.py` (se borra).
  Hecho cuando: `models.py` calcula `user_email_hash` con `consent_email_fingerprint`; los dos
  archivos borrados no existen; los tests de consentimientos pasan sin cambios (RF-012 de
  `consentimientos`, huella inmutable); suite verde.

- [x] T-011 Desaparece `consents/conf.py`
  RF: RF-002 | Depende de: T-010 | Archivos: 2
  Archivos: `consents/conf.py` (se borra), `consents/tests/test_conf.py` (se borra).
  Hecho cuando: los dos archivos no existen, nada importa `apps.consents.conf`
  (`grep -rn "consents.conf\|consents import conf" backend/apps` no devuelve nada) y sus casos
  (valor por defecto, ajuste, clave vacía y lectura del entorno) están en
  `core/tests/test_fingerprints.py` desde T-003; suite verde.

- [x] T-012 Test guardián de cálculos fuera del punto único
  RF: RF-010, RF-001 | Depende de: T-007, T-011 | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Hecho cuando: el test recorre `apps/` y `config/` sin las carpetas `tests/` ni
  `core/fingerprints.py`, y pasa sobre el código real con la única excepción
  (`accounts/password_validation.py`, `hashlib.sha1`); con fuentes sintéticas en `tmp_path`
  falla e indica el archivo para `import hashlib`, `from hmac import new as x`,
  `django.utils.crypto.salted_hmac`, una migración y `hashlib.sha256` en el archivo de la
  excepción; un mutante que vacíe la lista de usos prohibidos hace fallar los casos sintéticos;
  suite verde.
  Decisiones: (1) Un módulo prohibido usado sin atributo (por ejemplo, `getattr(hashlib, ...)`)
  cuenta como uso del módulo entero, que ninguna excepción cubre; y `from django.utils import
  crypto` se trata como un alias de `django.utils.crypto`. [Cierto] Revertir: quitar el último
  bucle de `forbidden_uses` y la rama `elif _is_forbidden(full_name)`. (2) No detecta imports
  dinámicos (`importlib.import_module("hashlib")`, `__import__`): queda como límite conocido del
  guardián. [Cierto] Revertir: no aplica. (3) Comprobado que el guardián habría marcado el
  `codes.py` anterior a T-007 (`hashlib.sha256`, `hmac.compare_digest`, `hmac.new`). [Cierto]

- [x] T-013 Resumen de la feature
  RF: — (criterio de finalización) | Depende de: T-012 | Archivos: 1
  Archivos: `specs/huellas-hmac-unificadas/resumen.md` (en la raíz del repositorio).
  Hecho cuando: existe con qué se hizo, cómo probarlo con comandos copiables (`pytest` del módulo
  y del guardián, y `manage.py registration` y `manage.py password_reset` de extremo a extremo) y
  un marco teórico (HMAC frente a cifrado, por qué una huella no se descifra, separación por clave
  y por formato, y qué es una lista cerrada de excepciones).

- [x] T-014 Los resúmenes de las features afectadas remiten al punto único
  RF: — (criterio de finalización) | Depende de: T-013 | Archivos: 3
  Archivos: `specs/procesos-pendientes/resumen.md`, `specs/cambio-contrasena/resumen.md`,
  `specs/consentimientos/resumen.md`.
  Hecho cuando: cada uno indica, junto a su explicación de la huella, que el cálculo vive en
  `backend/apps/core/fingerprints.py` desde `huellas-hmac-unificadas`, y no queda en ellos ninguna
  mención a `codes.code_fingerprint`, `codes.verify_code`, `codes.account_stamp` ni
  `consents/hashing.py` como lugar del cálculo.

- [x] T-015 Corrección: una fecha de rotación imposible da el error de configuración de RF-008
  Tipo: corrección | Origen: validación de RF-008
  RF: RF-008 | Depende de: — | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Causa: `parse_datetime` lanza `ValueError` con fechas bien escritas pero imposibles, y
  `_previous_code_key_in_transition` no lo convierte en `ImproperlyConfigured`.
  Hecho cuando: añadir `2026-13-01T10:00:00+00:00` a la parametrización de
  `test_rotation_date_without_timezone_is_rejected_only_when_matching` falla antes del arreglo y
  pasa después con `ImproperlyConfigured` que nombra `REGISTRATION_CODE_SECRET_ROTATED_AT`; un
  mutante que quite la captura hace fallar ese caso; la suite completa sigue en verde.

- [x] T-016 Corrección: test de la clave de códigos leída del entorno y sello sin consultas a la base de datos
  Tipo: corrección | Origen: validación de RF-003
  RF: RF-003 | Depende de: — | Archivos: 1
  Archivos: `core/tests/test_fingerprints.py`.
  Causa: ningún test comprueba que `REGISTRATION_CODE_SECRET` se lee del entorno (ni que, sin la
  variable, vale `DJANGO_SECRET_KEY`), y el test de cero consultas no cubre el sello de cuenta.
  Hecho cuando: un test de subproceso, como los de consentimientos, comprueba ambos valores;
  `django_assert_num_queries(0)` cubre `account_stamp` y `account_stamp_matches`; la suite
  completa sigue en verde.
  Decisiones: tarea solo de tests sobre código ya correcto: los tests pasan desde el principio, y
  su utilidad se demostró con mutantes (leer otra variable de entorno, cambiar el valor por
  defecto y hacer una consulta dentro de `account_stamp_matches`, que falla por exceso de
  consultas). [Cierto] Revertir: borrar los tres tests nuevos.

- [x] T-017 Una clave anterior de solo espacios es un error de configuración
  RF: RF-008 | Depende de: T-015 | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Hecho cuando: con `REGISTRATION_CODE_SECRET_PREVIOUS="   "`, tanto `code_fingerprint` como
  `code_matches` (y `account_stamp` / `account_stamp_matches`) lanzan `ImproperlyConfigured` que
  nombra `REGISTRATION_CODE_SECRET_PREVIOUS`, con fecha de rotación válida y sin ella; una clave
  anterior vacía (`""`) se sigue ignorando sin error; el test falla antes del arreglo; un mutante
  que quite la comprobación de espacios hace fallar el test; suite verde.

- [x] T-018 El guardián recorre todo el backend y vigila los módulos internos y la firma del framework
  RF: RF-010 | Depende de: — | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Hecho cuando: con fuentes sintéticas en `tmp_path`, el escaneo marca e indica el archivo para
  `import _hashlib`, `import _sha256`, `from django.core import signing` y
  `django.core.signing.Signer`, en `manage.py` y en una carpeta nueva (`otra/x.py`); no marca
  `from django.contrib.auth.hashers import make_password`, ni nada dentro de `tests/`, de un
  `conftest.py`, de una carpeta oculta ni de `apps/core/fingerprints.py`; el test sobre el código
  real recorre `backend/` completo y pasa; cada caso nuevo falla antes de ampliar la lista; un
  mutante que vuelva a limitar el recorrido a `apps/` y `config/` hace fallar el caso de
  `manage.py`; suite verde.
  Decisiones: `from django.core import signing` solo se marca cuando se usa (`signing.dumps`),
  igual que cualquier módulo importado como alias; importarlo sin usarlo no calcula nada.
  [Cierto] Revertir: marcar también el import en `forbidden_uses`.

- [x] T-019 El guardián vigila las bibliotecas criptográficas declaradas como dependencia
  RF: RF-010 (D-08) | Depende de: T-018 | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Hecho cuando: con un `requirements.txt` sintético sin bibliotecas criptográficas, un archivo que
  importa `cryptography` no se marca; con `cryptography>=42` declarado (también a través de un
  `-r` a otro archivo de requisitos), el mismo archivo se marca con su uso; lo mismo para
  `pycryptodome` → `Crypto`; el test sobre el código real lee los `requirements*.txt` reales y
  pasa; un mutante que vacíe la tabla de bibliotecas conocidas hace fallar el caso declarado;
  suite verde.
  Decisiones: (1) En lugar de afirmar que los requirements reales no declaran ninguna biblioteca
  criptográfica (lo que haría fallar la suite solo por declararla, algo que D-08 no pide), un test
  comprueba que se leen los reales siguiendo `-r` (`django`, `django-allauth`, `pytest`).
  [Cierto] Revertir: borrar `test_real_requirements_are_read_including_included_files`. (2) Los
  nombres se normalizan a minúsculas y `_` → `-`, y se ignoran los comentarios, también tras un
  `-r`; un caso con comentario al final del `-r` mata el mutante que no los quitaba. [Cierto]

- [x] T-020 El resumen refleja las correcciones de la validación
  RF: — (criterio de finalización) | Depende de: T-015, T-016, T-017, T-019 | Archivos: 1
  Archivos: `specs/huellas-hmac-unificadas/resumen.md` (en la raíz del repositorio).
  Hecho cuando: el resumen dice que el guardián recorre todo `backend/`, enumera los módulos
  vigilados (incluidos los internos y `django.core.signing`), explica que solo vigila las
  bibliotecas criptográficas declaradas (S-07) y que las utilidades de contraseñas están
  permitidas, recoge en "Errores de configuración" la clave anterior de solo espacios y la fecha
  inexistente, y su paso de prueba del guardián sigue siendo copiable y correcto.

- [x] T-021 Corrección: el guardián detecta accesos desde cualquier paquete antepasado y sigue todas las formas de `-r`
  Tipo: corrección | Origen: validación de RF-010
  RF: RF-010 | Depende de: — | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Causa: `forbidden_uses` solo registra alias de imports cuyo nombre ya está prohibido y no
  reconstruye cadenas `a.b.c` desde un paquete padre; `_read_requirements` solo reconoce `-r ` y
  `--requirement ` seguidos de espacio.
  Hecho cuando: los casos sintéticos `import django.core` + `django.core.signing.dumps`,
  `import django` + `django.core.signing.dumps`, `from django import utils` +
  `utils.crypto.salted_hmac`, `-rbase.txt` y `--requirement=base.txt` fallan antes del arreglo y
  se marcan con su archivo después; `import django` + `django.conf.settings` no se marca (D-09);
  la suite completa sigue en verde.
  Decisiones: (1) El guardián informa del módulo vigilado más el primer nombre usado
  (`django.core.signing.dumps`), y un `import` con puntos de un módulo vigilado se sigue marcando
  aunque no se use; el caso antiguo `import django.core.signing` + `.Signer` se redujo al import,
  porque ahora daba dos usos y el uso por cadena ya lo cubren los casos nuevos. [Cierto] Revertir:
  restaurar ese caso con los dos usos esperados. (2) Mutante equivalente: quitar el `.` en
  `_is_ancestor` solo registra alias de más, y un alias solo se informa si la cadena resuelta es
  un elemento vigilado exacto. [Probable]

- [x] T-022 Corrección: el test de clave vacía comprueba que el error nombra exactamente `REGISTRATION_CODE_SECRET`
  Tipo: corrección | Origen: validación de RF-008
  RF: RF-008 | Depende de: — | Archivos: 1
  Archivos: `core/tests/test_fingerprints.py`.
  Causa: `match="REGISTRATION_CODE_SECRET"` también coincide con `_PREVIOUS` y `_ROTATED_AT`.
  Hecho cuando: el mutante que cambia el nombre del ajuste en el mensaje hace fallar el test; la
  suite completa sigue en verde.

- [x] T-023 Corrección: un caso sintético por cada módulo interno vigilado
  Tipo: corrección | Origen: validación de RF-010
  RF: RF-010 | Depende de: — | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Causa: se pueden quitar `_sha1`, `_sha2`, `_sha3`, `_sha512`, `_md5` o `_blake2` de la lista sin
  que falle ningún test; además la lista incluye `_sha256` y `_sha512`, que no existen en Python
  3.12, y le falta `_crypt` (RF-010 tras la 2.ª validación).
  Hecho cuando: la lista de módulos internos es exactamente `_hashlib`, `_sha1`, `_sha2`, `_sha3`,
  `_md5`, `_blake2` y `_crypt`, con un caso sintético por módulo; quitar cualquiera de ellos hace
  fallar algún test; la suite completa sigue en verde.

- [x] T-024 Una fecha de rotación futura es un error de configuración
  RF: RF-007, RF-008 | Depende de: T-022 | Archivos: 2
  Archivos: `core/fingerprints.py`, `core/tests/test_fingerprints.py`.
  Hecho cuando: con `REGISTRATION_CODE_SECRET_ROTATED_AT` un minuto en el futuro, `code_matches`
  y `account_stamp_matches` lanzan `ImproperlyConfigured` que nombra exactamente ese ajuste, tanto
  si la clave actual coincide como si no, con o sin clave anterior; el cálculo
  (`code_fingerprint`, `account_stamp`) no falla; el test falla antes del arreglo; un mutante que
  quite la comprobación de fecha futura hace fallar el test; suite verde.

- [ ] T-025 El guardián vigila `crypt`, los tokens del framework y reconoce los archivos de test por su nombre
  RF: RF-010 | Depende de: T-023 | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Hecho cuando: los casos sintéticos `import crypt` + `crypt.crypt` y
  `from django.contrib.auth.tokens import default_token_generator` se marcan con su archivo; un
  `apps/x/test_x.py` y un `apps/x/tests.py` con `import hmac` no se marcan; cada caso falla antes
  del cambio; un mutante que quite `django.contrib.auth.tokens` de la lista hace fallar su caso;
  suite verde.

- [ ] T-026 El guardián vigila las funciones de hash en base de datos y las cookies firmadas por su nombre
  RF: RF-010 (D-05) | Depende de: T-025 | Archivos: 1
  Archivos: `core/tests/test_fingerprint_guard.py`.
  Hecho cuando: se marcan con su archivo `from django.db.models.functions import SHA256`,
  `from django.db.models.functions.text import MD5`, `from django.db.models import functions` +
  `functions.SHA512`, `response.set_signed_cookie(...)` y `request.get_signed_cookie` (sin
  llamar); no se marcan `from django.db.models.functions import Lower` ni una clase propia que
  define `def get_signed_cookie(self)`; el test sobre el código real sigue pasando; cada caso
  falla antes del cambio; un mutante que vacíe la lista de atributos prohibidos hace fallar los
  casos de cookies; suite verde.

- [ ] T-027 El resumen refleja la lista cerrada de RF-010 y la fecha de rotación futura
  RF: — (criterio de finalización) | Depende de: T-021, T-022, T-023, T-024, T-026 | Archivos: 1
  Archivos: `specs/huellas-hmac-unificadas/resumen.md` (en la raíz del repositorio).
  Hecho cuando: el resumen enumera la lista cerrada de elementos vigilados de RF-010 (módulos,
  funciones de base de datos y cookies firmadas), explica el acceso desde paquetes antepasados y
  qué archivos cuentan como test, recoge S-08 y S-09 en los límites conocidos y la fecha futura
  en los errores de configuración, y su prueba del guardián sigue siendo copiable y correcta.

## RF sin tarea
Ninguno. RF-009 está obsoleto.
