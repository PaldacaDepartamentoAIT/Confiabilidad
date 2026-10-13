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
- **Errores de configuración** (RF-008): una clave vacía, o una clave anterior igual a la actual,
  impide calcular y comprobar. Una fecha de rotación mal formada impide **cualquier**
  comprobación, aunque la clave actual coincida. Esto es más estricto que antes, cuando el error
  solo aparecía si la clave actual no coincidía; se decidió así durante T-001. Una clave anterior
  sin fecha de rotación se ignora.
- **Guardián** (`backend/apps/core/tests/test_fingerprint_guard.py`, RF-010): analiza con `ast`
  todos los `.py` de `apps/` y `config/`, migraciones y comandos de gestión incluidos, y falla si
  alguno, fuera de los tests y del punto único, importa o usa `hashlib`, `hmac` o
  `django.utils.crypto`. La única excepción es `hashlib.sha1` en
  `apps/accounts/password_validation.py` (contraseñas filtradas). El mensaje de fallo indica el
  archivo y el uso.
- **Lo que desaparece:** las funciones de huella de `apps/accounts/codes.py` (que conserva
  `Purpose`, `generate_code` y `generate_public_id`), las lecturas de claves de
  `apps/accounts/conf.py`, y `apps/consents/hashing.py` y `apps/consents/conf.py`.

### Límites conocidos
- El guardián no ve imports dinámicos (`importlib.import_module("hashlib")`, `__import__`).
- Con RF-009 obsoleto, nada impide que un tipo de huella futuro, con la misma clave que otro,
  firme un texto con el mismo formato (S-03). Hoy no ocurre: cada tipo firma un formato distinto.
- Rotar `DJANGO_SECRET_KEY` sin haber definido `CONSENT_EMAIL_HASH_SECRET` rompe las huellas de
  consentimiento guardadas (S-04). No cambia con esta feature.

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
