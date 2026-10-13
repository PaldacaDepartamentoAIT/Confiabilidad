# Plan: huellas-hmac-unificadas
Estado: aprobado

## Módulos
### M-01 Punto único de cálculo (`apps/core/fingerprints.py`)
Responsabilidad: el único sitio del backend que calcula y comprueba huellas con clave. Contiene
una sola primitiva privada que firma (HMAC-SHA256 en hexadecimal) y una sola que compara en tiempo
constante probando la clave actual y, si procede, la anterior. Encima, una función pública por
tipo de huella que compone su mensaje y llama a esas primitivas:
- `code_fingerprint(purpose, public_id, code)` / `code_matches(...)`: mensaje
  `"{purpose}:{public_id}:{code}"`, clave de códigos.
- `account_stamp(email, password_hash)` / `account_stamp_matches(...)`: mensaje
  `"password_reset_account:{correo normalizado}:{password_hash}"`, clave de códigos.
- `consent_email_fingerprint(email)` / `consent_email_matches(...)`: mensaje
  `"{correo normalizado}"`, clave de consentimientos.

`purpose` se recibe como `str` (los valores de `codes.Purpose`, que es un `StrEnum`) para que
`core` no dependa de `accounts`.
RF: RF-001, RF-004, RF-005, RF-006

### M-02 Claves y política por tipo (`apps/core/fingerprints.py`)
Responsabilidad: leer de `settings` (que las toma del entorno; en producción, de SOPS) la clave
de cada tipo y aplicar su política. Clave de códigos: `REGISTRATION_CODE_SECRET`, con
`REGISTRATION_CODE_SECRET_PREVIOUS`, `REGISTRATION_CODE_SECRET_ROTATED_AT` y
`REGISTRATION_SECRET_TRANSITION_MINUTES`. Clave de consentimientos: `CONSENT_EMAIL_HASH_SECRET`,
sin clave anterior. Los nombres de los ajustes y sus valores por defecto no cambian (S-04). Los
errores de configuración (`ImproperlyConfigured`, mensajes en inglés con `gettext_lazy` que
nombran el ajuste) son: clave actual vacía o de solo espacios, clave anterior de solo espacios
(haya o no fecha de rotación) y clave anterior igual a la actual, al calcular y al comprobar;
fecha de rotación mal formada, sin zona horaria, inexistente (el `ValueError` que lanza
`parse_datetime` con una fecha bien escrita que no existe se convierte en este error) o posterior
a `timezone.now()` sin margen (S-09), en toda comprobación, aunque la clave actual coincida. Una
clave anterior vacía (`""`), o una válida sin fecha de rotación, se ignora.
Sustituye a `code_secret`, `previous_code_secret`, `secret_rotated_at` y `secret_transition` de
`apps/accounts/conf.py` y a `apps/consents/conf.py`.
RF: RF-002, RF-003, RF-007, RF-008

### M-03 Adaptación de los usos (`apps/accounts/processes.py`, `apps/accounts/password_reset.py`, `apps/consents/models.py`)
Responsabilidad: llamar a M-01 en lugar de a `apps/accounts/codes.py` (huellas) y a
`apps/consents/hashing.py`. `codes.py` conserva `Purpose`, `generate_code` y
`generate_public_id`, y pierde todo lo que firma o compara. `apps/consents/hashing.py` y
`apps/consents/conf.py` se borran.
RF: RF-001

### M-04 Test guardián (`apps/core/tests/test_fingerprint_guard.py`)
Responsabilidad: recorrer todos los `.py` de `backend/` (`manage.py`, `apps/`, `config/`,
migraciones, comandos de gestión y cualquier carpeta futura), excluir los archivos de test (las
carpetas `tests/`, los `conftest.py`, `test_*.py` y `tests.py`), las carpetas ocultas
(`.mypy_cache`, `.pytest_cache`…) y el propio M-01, analizar cada archivo con `ast` y fallar si
usa un elemento vigilado de RF-010, directamente o desde cualquier paquete antepasado (D-09):
- módulos prohibidos enteros: `hashlib`, `hmac`, `crypt`, `_hashlib`, `_sha1`, `_sha2`, `_sha3`,
  `_md5`, `_blake2`, `_crypt`, `django.utils.crypto`, `django.core.signing`,
  `django.contrib.auth.tokens` y las bibliotecas criptográficas declaradas (D-08); hoy, ninguna;
- nombres prohibidos dentro de un módulo permitido: `MD5`, `SHA1`, `SHA224`, `SHA256`, `SHA384` y
  `SHA512` importados o usados desde `django.db.models.functions` o cualquiera de sus submódulos;
  el resto del módulo (por ejemplo, `Lower`) sigue permitido;
- atributos prohibidos por nombre, sobre cualquier objeto: `set_signed_cookie` y
  `get_signed_cookie` (C-11); definir un método propio con ese nombre no cuenta.

`django.contrib.auth.hashers` (utilidades de contraseñas) no está prohibido (C-08). La lista
cerrada de excepciones vive en el propio test como pares (archivo, uso): hoy, solo
(`apps/accounts/password_validation.py`, `hashlib.sha1`). El mensaje de fallo lista cada archivo
y el uso encontrado. No detecta módulos cargados por su nombre en texto (S-06).
RF: RF-010

### M-05 Documentación (`specs/huellas-hmac-unificadas/resumen.md` y resúmenes afectados)
Responsabilidad: crear el resumen de esta feature con su marco teórico, y añadir en los resúmenes
de `procesos-pendientes`, `cambio-contrasena` y `consentimientos` una línea que remita al punto
único de cálculo.
RF: — (criterio de finalización)

## Modelo de datos
Sin cambios: ni tablas, ni columnas, ni migraciones. Las columnas `code_hash`
(`PendingRegistration` y `PasswordResetRequest`), `account_stamp` (`PasswordResetRequest`) y
`user_email_hash` (`UserTerms` y `MarketingConsent`) conservan sus valores (RF-005).

## Decisiones
### D-01 Ubicación del punto único
Elegida: un módulo nuevo en la app `core` (`apps/core/fingerprints.py`).
Descartada: dejarlo en `apps/accounts/codes.py` y que `consents` lo importe.
Motivo: `consents` dependería de `accounts` solo para firmar, y el sitio "de las huellas" quedaría
mezclado con la generación de códigos. `core` ya es la app transversal y no depende de ninguna
otra.

### D-02 Forma de la API
Elegida: una primitiva privada de firma y otra de comparación, más funciones públicas tipadas
por tipo de huella que componen el mensaje.
Descartada: una única función pública genérica, `fingerprint(kind, *parts)`.
Motivo: con partes posicionales, intercambiar `public_id` y `code` compila y produce una huella
válida pero distinta, y la correlación se rompe sin avisar: justo el problema que esta feature
quiere evitar. Las funciones tipadas lo hacen imposible con mypy estricto (P-07). El cálculo sigue
pasando por una única función, y los formatos de mensaje viven todos en el mismo módulo.

### D-03 Nombres y valores de los ajustes
Elegida: conservar los nombres de los ajustes y sus valores por defecto.
Descartada: renombrarlos a un esquema común (`FINGERPRINT_CODES_SECRET`…).
Motivo: un cambio de nombre obliga a tocar `.env`, SOPS y el VPS, y si se olvida en producción se
cae al valor por defecto y las huellas guardadas dejan de coincidir. Además, está fuera de
alcance (S-04).

### D-04 Normalización del correo
Elegida: una única función privada (sin espacios a los lados y en minúsculas), usada por el sello
de cuenta y por la huella de consentimientos.
Descartada: conservar `lower()` para el sello.
Motivo: lo pide RF-004, y C-01 decidió que prevalece sobre RF-005. Los correos de `User` ya se
guardan así (`apps/accounts/models.py`), de modo que en la práctica no cambia ningún sello (S-02).

### D-05 Cómo detecta el guardián
Elegida: análisis estático con `ast` de los imports y de los accesos `módulo.atributo`, con
excepciones por (archivo, uso). Tres reglas: módulo prohibido entero, nombre prohibido dentro de
un módulo permitido (las funciones de hash en base de datos) y atributo prohibido por nombre sobre
cualquier objeto (las cookies firmadas), porque esos métodos se llaman sobre la petición o la
respuesta y no hay import que vigilar.
Descartada: buscar texto con expresiones regulares, o una regla de ruff.
Motivo: el texto da falsos positivos en comentarios y cadenas y no ve `from hashlib import
sha256 as x`. Ruff no tiene una regla que prohíba un import salvo en un archivo concreto sin
añadir configuración que el CI no ejercita como test. Con `ast` la excepción es por uso, no por
archivo: `password_validation.py` puede usar `hashlib.sha1`, pero no `hashlib.sha256`.

### D-06 Referencia independiente en los tests
Elegida: para cada tipo de huella, un vector fijo (clave, entradas y huella hexadecimal escrita
literalmente en el test), además de los cálculos HMAC a mano que ya existen.
Descartada: comparar solo con un HMAC calculado en el test.
Motivo: un cálculo en el test puede repetir el mismo error de formato que el código. Un valor
literal, generado una vez con el código actual antes del refactor, demuestra RF-005: si cambia un
solo byte del mensaje, el test falla.

### D-07 Comprobación de la huella de consentimientos
Elegida: añadir `consent_email_matches` aunque hoy nadie la use.
Descartada: ofrecer solo el cálculo para ese tipo.
Motivo: lo pide RF-006 (C-06: comprobación para todos los tipos), y así nadie compara esa huella
con `==` cuando haga falta.

### D-08 Bibliotecas criptográficas declaradas
Elegida: el guardián lee `backend/requirements*.txt` y, para cada dependencia declarada que esté
en una tabla cerrada de bibliotecas criptográficas conocidas (`cryptography` → `cryptography`,
`pycryptodome` → `Crypto`, `pycryptodomex` → `Cryptodome`, `pynacl` → `nacl`), añade su módulo
de import a los prohibidos. Hoy no se declara ninguna, así que no añade nada; si alguien declara
`cryptography`, sus usos pasan a hacer fallar la suite sin tocar el test.
Descartada: prohibir siempre `cryptography` y las demás, estén declaradas o no.
Motivo: C-07 decidió vigilar solo las declaradas (S-07). Leer los requirements en lugar de fijar
la lista evita que el guardián se quede atrás el día que se declare una. Una biblioteca que no
esté en la tabla no se vigila: la tabla se amplía con un cambio de esta spec.

### D-09 Acceso desde un paquete antepasado
Elegida: registrar como alias cualquier import cuyo nombre sea prefijo de un elemento vigilado
(`import django`, `import django.core`, `from django import utils`) y reconstruir la cadena
completa de atributos (`django.core.signing.dumps`) antes de compararla con la lista.
Descartada: marcar todo import de un paquete antepasado (`import django`).
Motivo: casi todo el backend importa `django`; marcarlo haría imposible la suite. Reconstruir la
cadena solo marca el uso real del elemento vigilado (C-14).

## Estrategia de tests
- **Unitario (`apps/core/tests/test_fingerprints.py`)**: vectores fijos de los cuatro mensajes
  (registro, cambio de contraseña, sello y consentimiento) (RF-001, RF-005); normalización del
  correo en el sello y en el consentimiento (RF-004); comparación en tiempo constante espiando la
  primitiva de M-01 para los tres tipos (RF-006); rotación: la clave anterior se acepta dentro
  del periodo y se rechaza fuera, y el consentimiento nunca usa clave anterior (RF-002, RF-007);
  todos los casos de error de RF-008 (clave vacía o de espacios, clave anterior de espacios con
  y sin fecha, clave anterior igual a la actual, fecha mal formada, sin zona horaria o
  inexistente o futura, también cuando la clave actual coincide); ninguna consulta a la base de
  datos al calcular ni al comprobar, con `django_assert_num_queries(0)` de pytest-django (RF-003). Los tests de
  `apps/accounts/tests/test_codes.py`, `apps/consents/tests/test_hashing.py`,
  `apps/consents/tests/test_conf.py` y la parte de secretos de
  `apps/accounts/tests/test_registration_conf.py` se reescriben o se mueven aquí, sin perder
  ningún RF de sus features (C-05).
- **Guardián (`apps/core/tests/test_fingerprint_guard.py`)**: el test sobre el código real
  (RF-010), más casos con fuentes sintéticas en `tmp_path` (import directo, `from … import …
  as`, cada módulo prohibido entero, `import django` e `import django.core` seguidos de
  `django.core.signing.dumps`, `from django import utils`, `SHA256` desde
  `django.db.models.functions` y `MD5` desde su submódulo `text`, `Lower` permitido,
  `response.set_signed_cookie` y `request.get_signed_cookie`, `manage.py`, una carpeta nueva,
  `test_x.py` y `tests.py` fuera de `tests/` sin marcar, excepción permitida, excepción con otro
  uso, `django.contrib.auth.hashers` permitido, y `cryptography` permitido sin declarar y
  prohibido al declararlo en un `requirements.txt` sintético, también con `-rbase.txt` y
  `--requirement=base.txt`) para demostrar que detecta e indica el archivo.
- **Integración (suites existentes)**: `test_processes.py`, `test_registration_service.py`,
  `test_password_reset_service.py`, sus comandos y los tests de consentimientos deben pasar. Solo
  se tocan sus rutas de `monkeypatch` u `override_settings` si apuntan a lo movido.
- **CLI (P-03)**: `pytest` y los comandos `manage.py registration` y `manage.py password_reset`,
  que ejercitan el cálculo y la comprobación de extremo a extremo.
- **Mutación**: para cada tarea, un mutante en M-01 (por ejemplo, cambiar `:` por `;` en un
  mensaje o quitar `strip()`) debe hacer fallar un vector fijo.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-03 | Unitario (vectores) + guardián (RF-010) + integración |
| RF-002 | M-02 | Unitario |
| RF-003 | M-02 | Unitario (sin consultas a BD) |
| RF-004 | M-01 | Unitario |
| RF-005 | M-01 | Unitario (vectores fijos, D-06) + integración |
| RF-006 | M-01 | Unitario (espía de la comparación) |
| RF-007 | M-02 | Unitario |
| RF-008 | M-02 | Unitario |
| RF-009 | — | OBSOLETO |
| RF-010 | M-04 (D-05, D-08, D-09) | Guardián (código real + fuentes sintéticas + requirements sintéticos) |

## RF sin cobertura
Ninguno. RF-009 está obsoleto y no se diseña.
