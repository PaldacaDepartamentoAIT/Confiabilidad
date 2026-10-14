# Spec: huellas-hmac-unificadas
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
Hoy las huellas con clave de correos y códigos se calculan en dos sitios distintos, cada uno con
su propia forma de normalizar el correo. Si dos partes del código calculan una huella de forma
distinta, la correlación entre tablas se rompe sin avisar: el mismo correo deja de producir la
misma huella. Esta feature reúne todo el cálculo en un único punto de cálculo compartido, sin
cambiar ninguna huella ya guardada, y hace que la suite de tests detecte cualquier cálculo nuevo
fuera de él.

Una huella no se descifra: solo se recalcula a partir del valor original y se compara con la
guardada.

Desde el 2026-10-14, el punto único también calcula la máscara con la que
`correo-asincrono-plantillas` oculta el código de un correo pendiente (RF-011). La máscara no es una
huella: con su clave se deshace.

Cumple RNF-25 (*Las claves hash no deben estar en la base de datos*): «Se debe usar un HMAC con
una clave en el almacén de secretos, nunca en la base de datos» (ver S-01).

## Requisitos funcionales
### RF-001 Punto único de cálculo
El sistema deberá calcular toda huella con clave de correos, códigos y sellos de cuenta, y la
máscara del código de los correos pendientes (RF-011), mediante un único punto de cálculo
compartido.

### RF-002 Clave y política de rotación por tipo de huella
El sistema deberá asociar cada tipo de huella a su clave y a su política de rotación:
- huella del código de un proceso (registro y cambio de contraseña) y sello de cuenta: clave de
  códigos, que admite rotación con periodo de transición;
- huella del correo en consentimientos: clave de consentimientos, que no rota.

### RF-003 Clave fuera de la base de datos (RNF-25)
El sistema deberá obtener la clave de cada tipo de huella, y la de la máscara (RF-011), del
almacén de secretos (la configuración del entorno) y nunca guardarla en la base de datos ni leerla
de ella.

### RF-004 Normalización única del correo
Cuando una huella incluya un correo, el sistema deberá normalizarlo siempre de la misma forma:
sin espacios al principio ni al final y en minúsculas.

### RF-005 Compatibilidad con las huellas guardadas
El sistema deberá producir, para cada huella ya guardada, exactamente el mismo valor que producía
antes de esta feature, sin migrar ni recalcular datos. La única excepción es un sello de cuenta
calculado con un correo sin normalizar: prevalece la normalización única (RF-004) y esa solicitud
de cambio de contraseña deja de valer.

### RF-006 Comprobación de una huella
Cuando se compruebe un valor contra una huella guardada de cualquier tipo, el sistema deberá
recalcular la huella del valor y compararla con la guardada en tiempo constante.

### RF-007 Clave anterior durante la transición
Mientras dure el periodo de transición tras rotar la clave de un tipo que admite rotación, el
sistema deberá aceptar en la comprobación (RF-006) tanto las huellas calculadas con la clave
actual como las calculadas con la anterior, y fuera de ese periodo solo las de la clave actual.

### RF-008 Clave mal configurada
Si la clave de un tipo de huella está vacía, si la clave anterior está definida pero solo contiene
espacios (haya o no fecha de rotación), o si la clave anterior coincide con la actual, entonces el
sistema deberá rechazar el cálculo y la comprobación con un error de configuración que nombre la
clave afectada. Si la fecha de rotación no es una fecha válida con zona horaria (incluida una fecha
bien escrita pero que no existe) o es posterior al momento de la comprobación, sin margen para
desfases de reloj (S-09), entonces el sistema deberá rechazar la comprobación con un error de
configuración que nombre ese ajuste. Si hay una clave anterior válida pero no fecha de rotación,
entonces el sistema deberá ignorar la clave anterior en la comprobación.

### RF-009 Huellas distintas entre tipos — OBSOLETO
OBSOLETO (2026-10-09, C-03): «un mismo valor de entrada» no tiene una lectura única, porque cada
tipo recibe datos de forma distinta. La separación entre tipos se confía a sus claves (RF-002) y
el riesgo queda en S-03. Texto original: ~~El sistema deberá producir huellas distintas para un
mismo valor de entrada en tipos de huella distintos, aunque sus claves coincidan.~~

### RF-010 Detección de cálculos fuera del punto único
Si algún archivo Python del backend (incluidos `manage.py`, las migraciones, los comandos de
gestión y cualquier carpeta futura), fuera del punto único de cálculo y de los archivos de test,
usa alguno de los elementos vigilados, directamente o a través de cualquiera de sus paquetes
antepasados (por ejemplo, `import django.core` o `import django` seguidos de
`django.core.signing.dumps`), entonces la suite de tests deberá fallar e indicar el archivo y el
uso.

Elementos vigilados (lista cerrada):
- biblioteca estándar: `hashlib`, `hmac`, `crypt` y los módulos internos de hash de Python 3.12
  (`_hashlib`, `_sha1`, `_sha2`, `_sha3`, `_md5`, `_blake2` y `_crypt`);
- framework: `django.utils.crypto`, `django.core.signing` y `django.contrib.auth.tokens`;
- funciones de hash en base de datos del framework: `MD5`, `SHA1`, `SHA224`, `SHA256`, `SHA384` y
  `SHA512`, importadas desde `django.db.models.functions` o desde cualquiera de sus submódulos;
  el resto de funciones de ese módulo sigue permitido;
- métodos de cookies firmadas, por su nombre: cualquier acceso a un atributo llamado
  `set_signed_cookie` o `get_signed_cookie`, se llame o no (definir un método propio con ese
  nombre no cuenta);
- las bibliotecas criptográficas de la tabla cerrada del plan que estén declaradas como
  dependencia del proyecto (S-07).

Son archivos de test los que están dentro de una carpeta `tests/`, los `conftest.py` y los que
pytest recoge como test (`test_*.py` y `tests.py`).

Excepciones (lista cerrada):
- la comprobación de contraseñas filtradas, que exige un hash sin clave.

Añadir un elemento vigilado o una excepción es un cambio de esta spec. Fuera de la lista vigilada
no se garantiza la detección: módulos cargados por su nombre en texto (S-06), bibliotecas no
declaradas o fuera de la tabla (S-07), funciones prohibidas que llegan reexportadas por un módulo
permitido y utilidades que calculan un hash por dentro (S-08), y las utilidades de contraseñas del
framework, que no calculan huellas con clave.

### RF-011 Máscara del código de un correo pendiente
Cuando se oculte el código de 6 dígitos de un correo pendiente, el sistema deberá combinarlo con una
máscara calculada con la clave de la máscara y un valor aleatorio propio de ese correo, que no se
repite, de modo que solo pueda recuperarse con esa clave y ese valor. La clave de la máscara es
propia, distinta de la de códigos, y no rota. Si la clave de la máscara está vacía, solo contiene
espacios o coincide con la clave de códigos, entonces el sistema deberá rechazar ocultar y
recuperar el código con un error de configuración que nombre esa clave.

## Supuestos
- S-01 RNF-25 procede de un documento de requisitos externo al repositorio. La spec lo cita con
  su texto literal y no se crea la categoría `RNF` en las convenciones del proyecto.
  *Riesgo:* si ese documento cambia, la cita queda desactualizada sin aviso.
- S-02 Los correos guardados ya están normalizados (sin espacios y en minúsculas), así que
  unificar la normalización (RF-004) no cambia en la práctica ninguna huella guardada. Si alguno
  no lo está, se aplica la excepción de RF-005: esa solicitud de cambio de contraseña deja de
  valer y hay que pedir otra. Las huellas de consentimiento no se ven afectadas: ya usaban esta
  normalización.
- S-03 Dos tipos de huella pueden compartir el mismo valor de clave (hoy ocurre si no se define
  ninguna, porque las dos toman el mismo valor por defecto); no se impide. *Riesgo:* con RF-009
  obsoleto, nada garantiza que dos tipos con la misma clave no produzcan la misma huella. Hoy no
  ocurre, porque cada tipo firma un texto con formato distinto, pero un tipo futuro podría
  romperlo.
- S-04 Se mantiene de dónde sale cada clave y su valor por defecto actual. *Riesgo:* si no se
  define la clave de consentimientos y se cambia el valor por defecto del que depende, las huellas
  de consentimiento guardadas dejan de coincidir.
- S-05 La clave de consentimientos sigue sin rotar (S-09 de `consentimientos`).
- S-06 Nadie carga a propósito un módulo de hash por su nombre en texto para esquivar la detección
  de RF-010. *Riesgo:* ese uso pasaría la suite sin aviso; queda a cargo de la revisión de código.
- S-07 Hoy el proyecto no declara ninguna biblioteca criptográfica; `cryptography` está instalada
  solo como dependencia de otras y RF-010 no la vigila (C-07). *Riesgo:* una huella calculada con
  ella pasaría la suite sin aviso; queda a cargo de la revisión de código, y declararla como
  dependencia la pondría bajo vigilancia.
- S-08 Nadie calcula una huella con funciones que llegan reexportadas por un módulo permitido
  (por ejemplo, `hashers.hashlib.sha256`) ni con utilidades que calculan un hash por dentro (por
  ejemplo, `get_session_auth_hash`, `make_template_fragment_key` o `uuid.uuid5`). *Riesgo:* ese
  uso pasaría la suite sin aviso; queda a cargo de la revisión de código. RF-010 es una alarma
  sobre una lista cerrada, no una garantía de que no exista ningún hash fuera del punto único.
- S-09 Los servidores tienen el reloj sincronizado y `REGISTRATION_CODE_SECRET_ROTATED_AT` se fija
  con el momento real de la rotación o uno anterior, nunca con una rotación programada.
  *Riesgo:* un servidor con el reloj atrasado respecto a esa fecha rechaza todas las
  comprobaciones de huellas de código hasta alcanzarla (RF-008, C-12).
- S-10 Sin definir, la clave de la máscara vale `email-code:` seguido de `DJANGO_SECRET_KEY` (D-06
  de `correo-asincrono-plantillas`), así que es distinta de la de códigos aunque no se defina
  ninguna. No rota: si cambia, los correos de código pendientes recuperan un código que no coincide
  con su huella y se descartan; la persona puede reenviar. La integridad de la máscara la da esa
  comprobación de la huella, no la máscara.

## Fuera de alcance
- Los hashes que no son huellas con clave: la comprobación de contraseñas filtradas (excepción de
  RF-010) y el almacenamiento de contraseñas, que hace el propio framework fuera del código de la
  aplicación.
- Que los tests usen el punto único de cálculo: pueden calcular la huella esperada por su cuenta,
  como referencia independiente.
- Cambiar de dónde salen las claves, sus valores por defecto o hacerlas obligatorias (S-04).
- Rotar la clave de consentimientos (S-05).
- Recuperar un correo o un código a partir de su huella: no es posible por diseño. La máscara de
  RF-011 no es una huella.
- Cambiar el formato de cualquier huella existente o migrar huellas guardadas (RF-005).
- Añadir la categoría `RNF` a las convenciones del proyecto (S-01).
- Detectar módulos de hash cargados de forma dinámica a partir de su nombre en texto (RF-010, S-06).
- Vigilar bibliotecas criptográficas no declaradas como dependencia del proyecto (RF-010, S-07).
- Vigilar las utilidades de contraseñas del framework usadas desde el código de la aplicación
  (RF-010, C-08).
- Detectar cualquier hash fuera de la lista vigilada de RF-010: reexports y utilidades con hash
  interno (S-08).

## Criterios de finalización
- Ninguna huella con clave de correos, códigos o sellos de cuenta se calcula fuera del punto
  único (RF-001), y el test de RF-010 lo comprueba.
- Para cada tipo de huella, la huella esperada calculada a mano en los tests coincide con la del
  punto único (RF-005).
- Las suites de las features que usan huellas (`procesos-pendientes`, `cambio-contrasena` y
  `consentimientos`) pasan. Sus tests de huellas pueden reescribirse o fusionarse con los del
  punto único, siempre que cada RF de esas features siga cubierto por al menos un test.
- Suite completa, tipos y lint en verde, y cobertura de líneas ≥ 80%.
- Los resúmenes de las features afectadas reflejan el nuevo punto único de cálculo, y existe
  `specs/huellas-hmac-unificadas/resumen.md`.
- Un test comprueba que un código ocultado se recupera con la misma clave y el mismo valor, que dos
  correos no comparten valor aleatorio y que cada clave mal configurada de RF-011 da su error.

## Historial de cambios
- 2026-10-09 — Creación de la spec — RF: RF-001…RF-010 — Estado: clarificado
- 2026-10-09 — Clarificación C-01…C-06: excepción de normalización en RF-005, comprobación para
  todos los tipos, errores de rotación en RF-008, RF-009 obsoleto y alcance y excepciones de
  RF-010 — RF: RF-005, RF-006, RF-008, RF-009, RF-010 — Estado: clarificado
- 2026-10-13 — Cambio tras la validación: RF-010 amplía los usos detectados (módulos internos de
  la biblioteca estándar, firma de datos del framework y bibliotecas criptográficas instaladas) y
  acepta el límite de los módulos cargados de forma dinámica (S-06); RF-008 trata como error una
  clave anterior de solo espacios y precisa que una fecha de rotación inexistente es inválida —
  RF: RF-008, RF-010 — Estado: clarificado
- 2026-10-13 — Clarificación C-07…C-10: RF-010 vigila solo las bibliotecas criptográficas
  declaradas (S-07), permite las utilidades de contraseñas del framework y cubre todo el backend;
  RF-008 rechaza siempre una clave anterior de solo espacios — RF: RF-008, RF-010 — Estado:
  impacto analizado
- 2026-10-13 — Cambio tras la 2.ª validación: RF-010 pasa a ser una lista cerrada de elementos
  vigilados (añade `crypt`, `_crypt`, `django.contrib.auth.tokens`, las funciones de hash en base
  de datos y las cookies firmadas; quita los módulos internos que no existen en Python 3.12;
  detecta el acceso por el paquete padre; define los archivos de test) y acepta S-08; RF-008
  rechaza una fecha de rotación futura, que antes alargaba la vida de la clave anterior (RF-007) —
  RF: RF-007, RF-008, RF-010 — Estado: clarificado
- 2026-10-13 — Clarificación C-11…C-14: cookies firmadas por cualquier acceso, fecha futura sin
  margen (S-09), funciones de hash en base de datos desde cualquier submódulo y acceso desde
  cualquier paquete antepasado — RF: RF-008, RF-010 — Estado: impacto analizado
- 2026-10-14 — Cambio por `correo-asincrono-plantillas` (D-06): el punto único calcula también la
  máscara reversible del código de los correos pendientes — RF: RF-001 modificado; RF-011 añadido;
  objetivo, S-10, fuera de alcance y criterios ajustados. Clarificado (C-01, C-02): RF-003
  ajustado; RF-011 sin cambios — Estado: clarificado
