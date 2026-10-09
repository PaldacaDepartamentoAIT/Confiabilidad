# Spec: huellas-hmac-unificadas
Estado: borrador
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

Cumple RNF-25 (*Las claves hash no deben estar en la base de datos*): «Se debe usar un HMAC con
una clave en el almacén de secretos, nunca en la base de datos» (ver S-01).

## Requisitos funcionales
### RF-001 Punto único de cálculo
El sistema deberá calcular toda huella con clave de correos, códigos y sellos de cuenta mediante
un único punto de cálculo compartido.

### RF-002 Clave y política de rotación por tipo de huella
El sistema deberá asociar cada tipo de huella a su clave y a su política de rotación:
- huella del código de un proceso (registro y cambio de contraseña) y sello de cuenta: clave de
  códigos, que admite rotación con periodo de transición;
- huella del correo en consentimientos: clave de consentimientos, que no rota.

### RF-003 Clave fuera de la base de datos (RNF-25)
El sistema deberá obtener la clave de cada tipo de huella del almacén de secretos (la
configuración del entorno) y nunca guardarla en la base de datos ni leerla de ella.

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
Si la clave de un tipo de huella está vacía, o la clave anterior coincide con la actual, entonces
el sistema deberá rechazar el cálculo y la comprobación con un error de configuración que nombre
la clave afectada. Si la fecha de rotación no es una fecha con zona horaria, entonces el sistema
deberá rechazar la comprobación con un error de configuración que nombre ese ajuste. Si hay clave
anterior pero no fecha de rotación, entonces el sistema deberá ignorar la clave anterior en la
comprobación.

### RF-009 Huellas distintas entre tipos — OBSOLETO
OBSOLETO (2026-10-09, C-03): «un mismo valor de entrada» no tiene una lectura única, porque cada
tipo recibe datos de forma distinta. La separación entre tipos se confía a sus claves (RF-002) y
el riesgo queda en S-03. Texto original: ~~El sistema deberá producir huellas distintas para un
mismo valor de entrada en tipos de huella distintos, aunque sus claves coincidan.~~

### RF-010 Detección de cálculos fuera del punto único
Si algún código de la aplicación (incluidas las migraciones y los comandos de gestión, excluidos
los tests), fuera del punto único de cálculo, usa una función de hash criptográfico o de HMAC,
entonces la suite de tests deberá fallar e indicar el archivo en el que ocurre, salvo los usos de
esta lista cerrada de excepciones:
- la comprobación de contraseñas filtradas, que exige un hash sin clave.

Añadir una excepción es un cambio de esta spec.

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

## Fuera de alcance
- Los hashes que no son huellas con clave: la comprobación de contraseñas filtradas (excepción de
  RF-010) y el almacenamiento de contraseñas, que hace el propio framework fuera del código de la
  aplicación.
- Que los tests usen el punto único de cálculo: pueden calcular la huella esperada por su cuenta,
  como referencia independiente.
- Cambiar de dónde salen las claves, sus valores por defecto o hacerlas obligatorias (S-04).
- Rotar la clave de consentimientos (S-05).
- Recuperar un correo o un código a partir de su huella: no es posible por diseño.
- Cambiar el formato de cualquier huella existente o migrar huellas guardadas (RF-005).
- Añadir la categoría `RNF` a las convenciones del proyecto (S-01).

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

## Historial de cambios
- 2026-10-09 — Creación de la spec — RF: RF-001…RF-010 — Estado: clarificado
- 2026-10-09 — Clarificación C-01…C-06: excepción de normalización en RF-005, comprobación para
  todos los tipos, errores de rotación en RF-008, RF-009 obsoleto y alcance y excepciones de
  RF-010 — RF: RF-005, RF-006, RF-008, RF-009, RF-010 — Estado: clarificado
