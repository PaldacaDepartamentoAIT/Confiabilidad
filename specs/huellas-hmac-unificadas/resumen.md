# Resumen — huellas-hmac-unificadas
Estado: pendiente de validación · Última actualización: 2026-10-13

## Qué se hizo
Todas las huellas con clave del backend se calculan y se comprueban ahora en un único módulo,
`backend/apps/core/fingerprints.py` (RF-001). Antes había dos implementaciones independientes
(`apps/accounts/codes.py` y `apps/consents/hashing.py`), cada una con su propia forma de
normalizar el correo. Ninguna huella guardada cambia (RF-005), y un test hace fallar la suite si
alguien vuelve a calcular un hash fuera de ese módulo (RF-010).

- **Tres tipos de huella, dos claves** (RF-002):
  - código de un proceso (`code_fingerprint` / `code_matches`) y sello de cuenta
    (`account_stamp` / `account_stamp_matches`): clave `REGISTRATION_CODE_SECRET`, que admite
    rotación con `REGISTRATION_CODE_SECRET_PREVIOUS`, `REGISTRATION_CODE_SECRET_ROTATED_AT` y
    `REGISTRATION_SECRET_TRANSITION_MINUTES` (RF-007);
  - correo en consentimientos (`consent_email_fingerprint` / `consent_email_matches`): clave
    `CONSENT_EMAIL_HASH_SECRET`, que no rota nunca.
- **Las claves solo salen de la configuración del entorno** (en producción, cifradas con SOPS),
  nunca de la base de datos: calcular o comprobar una huella no hace ninguna consulta (RF-003,
  RNF-25). Los nombres de los ajustes y sus valores por defecto no cambian.
- **Una sola normalización del correo** (RF-004): sin espacios a los lados y en minúsculas, para
  el sello y para el consentimiento. El sello antes solo pasaba a minúsculas; como los correos de
  `User` ya se guardan normalizados, en la práctica no cambia ningún sello (S-02).
- **Comprobación en tiempo constante para todos los tipos** (RF-006), también para la huella de
  consentimientos, aunque hoy nadie la compare.
- **Errores de configuración** (RF-008): una clave vacía o de solo espacios, una clave anterior
  de solo espacios (haya o no fecha de rotación) o una clave anterior igual a la actual impiden
  calcular y comprobar. Una fecha de rotación mal formada, sin zona horaria, que no existe (por
  ejemplo, `2026-13-01T10:00:00+00:00`) o posterior al momento actual, sin ningún margen, impide
  **cualquier** comprobación, aunque la clave actual coincida. Esto es más estricto que antes, cuando el error solo aparecía si la clave actual no
  coincidía; se decidió así durante T-001. Una clave anterior vacía, o una válida sin fecha de
  rotación, se ignora.
- **Guardián** (`backend/apps/core/tests/test_fingerprint_guard.py`, RF-010): analiza con `ast`
  todos los `.py` de `backend/` (`manage.py`, `apps/`, `config/`, migraciones, comandos de gestión
  y cualquier carpeta nueva), salvo los archivos de test (carpetas `tests/`, `conftest.py`,
  `test_*.py` y `tests.py`), las carpetas ocultas y el punto único. Falla si alguno usa un elemento
  de esta **lista cerrada**:
  - módulos enteros: `hashlib`, `hmac`, `crypt`, los módulos internos de hash de Python 3.12
    (`_hashlib`, `_sha1`, `_sha2`, `_sha3`, `_md5`, `_blake2`, `_crypt`), `django.utils.crypto`,
    `django.core.signing` y `django.contrib.auth.tokens`;
  - las funciones de hash en base de datos `MD5`, `SHA1`, `SHA224`, `SHA256`, `SHA384` y `SHA512`
    de `django.db.models.functions` o de sus submódulos (el resto de funciones, como `Lower`, está
    permitido);
  - cualquier acceso a un atributo `set_signed_cookie` o `get_signed_cookie` (cookies firmadas);
  - una biblioteca criptográfica **declarada** en `backend/requirements*.txt` (siguiendo `-r` en
    todas sus formas): `cryptography`, `pycryptodome`, `pycryptodomex` o `pynacl`. Hoy no se
    declara ninguna (S-07).

  El uso cuenta tanto directo como a través de cualquier paquete antepasado: `import django`
  seguido de `django.core.signing.dumps(...)` se marca, pero `django.conf.settings` no. Las
  utilidades de contraseñas del framework (`django.contrib.auth.hashers`) están permitidas. La
  única excepción es `hashlib.sha1` en `apps/accounts/password_validation.py` (contraseñas
  filtradas). El mensaje de fallo indica el archivo y el uso.
- **Lo que desaparece:** las funciones de huella de `apps/accounts/codes.py` (que conserva
  `Purpose`, `generate_code` y `generate_public_id`), las lecturas de claves de
  `apps/accounts/conf.py`, y `apps/consents/hashing.py` y `apps/consents/conf.py`.

### Límites conocidos
- El guardián no ve imports dinámicos (`importlib.import_module("hashlib")`, `__import__`) (S-06).
- `cryptography` está instalada como dependencia de otras bibliotecas, pero no declarada, así que
  el guardián no la vigila (S-07). Si se declara en `requirements.txt`, pasa a vigilarse sola.
  Una biblioteca criptográfica que no esté en la tabla del guardián tampoco se vigila: añadirla es
  un cambio de la spec.
- Con RF-009 obsoleto, nada impide que un tipo de huella futuro, con la misma clave que otro,
  firme un texto con el mismo formato (S-03). Hoy no ocurre: cada tipo firma un formato distinto.
- Rotar `DJANGO_SECRET_KEY` sin haber definido `CONSENT_EMAIL_HASH_SECRET` rompe las huellas de
  consentimiento guardadas (S-04). No cambia con esta feature.
- El guardián es una alarma sobre una lista cerrada, no una garantía (S-08): no ve funciones
  prohibidas que llegan reexportadas por un módulo permitido (por ejemplo,
  `hashers.hashlib.sha256`) ni utilidades que calculan un hash por dentro (`get_session_auth_hash`,
  `make_template_fragment_key`, `uuid.uuid5`). Eso queda a cargo de la revisión de código.
- `REGISTRATION_CODE_SECRET_ROTATED_AT` debe ser el momento real de la rotación o uno anterior,
  nunca una rotación programada, y los servidores deben tener el reloj sincronizado (S-09): con
  una fecha futura, todas las comprobaciones de huellas de código fallan hasta alcanzarla.

## Cómo probarlo
Todo se hace desde `backend/`, sin frontend.

1. Ejecuta los tests del punto único:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest apps/core/tests/test_fingerprints.py --no-cov
   ```
   Deberías ver todos los tests en verde. Incluyen cuatro vectores fijos (huellas escritas
   literalmente, calculadas con el código anterior a esta feature) que fallan si cambia un solo
   byte de un mensaje.

2. Ejecuta el guardián:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest apps/core/tests/test_fingerprint_guard.py --no-cov
   ```
   Deberías ver todos los tests en verde. Para verlo fallar, crea un archivo que calcule un hash
   por su cuenta:
   ```bash
   printf 'import hashlib\nhashlib.sha256(b"x")\n' > backend/apps/core/hash_prohibido.py
   ```
   Vuelve a ejecutar el guardián con el mismo comando del paso 2. Deberías ver un fallo que
   termina en `apps/core/hash_prohibido.py: hashlib.sha256`. Borra el archivo:
   ```bash
   rm backend/apps/core/hash_prohibido.py
   ```

3. Recorre un registro de extremo a extremo, que calcula y comprueba la huella del código con el
   punto único. Levanta la base de datos y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   Empieza un registro:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email huella@example.com --name "Ana Huella" --birthdate 1990-01-01 --country es
   ```
   Deberías ver `public_id: …` y `code: …`. En el comando siguiente, `<PUBLIC_ID>` y `<CODE>` son
   esos dos valores:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
   ```
   Deberías ver `public_id: …` y `Code verified.`. Repite la verificación con un código
   incorrecto:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> 000000
   ```
   Deberías ver `The code was already verified.`, porque el proceso ya quedó validado. Si lo
   pruebas en un registro nuevo antes del código correcto, deberías ver `Wrong code.`.

4. Si tienes datos de antes de esta feature, comprueba que sus huellas de consentimiento siguen
   coincidiendo (RF-005):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.consents.models import UserTerms; from apps.core import fingerprints; rows = UserTerms.objects.exclude(user=None).select_related('user'); print(sum(not fingerprints.consent_email_matches(r.user.email, r.user_email_hash) for r in rows), 'of', rows.count())"
   ```
   Deberías ver `0 of <N>`, donde `<N>` es el número de aceptaciones con usuario. Un número
   distinto de 0 solo es normal si alguna de esas personas cambió de correo después de aceptar:
   la huella se calcula al aceptar y no cambia nunca.

5. Ejecuta la suite completa:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend pytest
   ```
   Deberías ver todos los tests en verde y la cobertura por encima del 80 %.

## Marco teórico
### Una huella HMAC no se descifra
Cifrar es reversible: con la clave se recupera el original. Un HMAC no lo es. Mezcla el dato (un
correo, un código) con una clave secreta y produce un resumen de longitud fija del que no se puede
sacar el dato. Para saber si una huella corresponde a un correo, se vuelve a calcular la huella de
ese correo con la misma clave y se comparan. Por eso el módulo ofrece dos operaciones por tipo:
**calcular** y **comprobar**. No existe "descifrar", ni puede existir.

### Por qué una sola función
Si dos partes del código calculan la "misma" huella de forma distinta (una quita espacios y la
otra no, una pone un prefijo y la otra no), producen valores distintos para el mismo dato, y las
tablas que deberían cruzarse por esa huella dejan de coincidir sin ningún error. Con un único
módulo, el formato de cada mensaje está escrito en un solo sitio, y el guardián impide que
aparezca un segundo.

### Separación por clave y por formato
Dos tipos de huella no deben poder confundirse. Aquí se separan de dos maneras: por **clave**
(los consentimientos usan una clave distinta a la de los códigos) y por **formato** (cada tipo
firma un texto con un prefijo propio: `registration:…`, `password_reset:…`,
`password_reset_account:…`). Si dos tipos compartieran clave y formato, una huella de uno podría
pasar por una del otro.

### Comparación en tiempo constante
Comparar dos textos carácter a carácter y parar en la primera diferencia tarda más cuanto más se
parecen, y un atacante puede medir esa diferencia para adivinar una huella poco a poco.
`hmac.compare_digest` tarda siempre lo mismo, se parezcan o no.

### Vectores fijos
Un test que calcula la huella esperada con la misma fórmula que el código puede repetir el mismo
error. Un vector fijo es una huella escrita literalmente en el test, calculada una vez con el
código anterior al refactor. Si el formato cambia un solo byte, el test falla. Es lo que demuestra
que las huellas ya guardadas siguen valiendo.

### Lista cerrada de excepciones
El guardián prohíbe por defecto cualquier hash criptográfico fuera del punto único y solo permite
los usos que aparecen en una lista escrita en el propio test. "Cerrada" quiere decir que añadir un
uso no basta con tocar el código: es un cambio de la spec (RF-010), y alguien tiene que justificar
por qué ese hash no es una huella con clave. Hoy la lista tiene una entrada: el SHA-1 que exige el
servicio de contraseñas filtradas.
