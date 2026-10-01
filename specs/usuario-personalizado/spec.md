# Spec: usuario-personalizado
Estado: aprobada

## Objetivo (por qué)
El usuario del sistema ya existe como modelo propio (feature `auth-headless`), pero solo guarda el
correo. Esta feature le añade los datos personales que el dominio necesita (nombre, fecha de
nacimiento y país), hace que la regla "un correo, una cuenta" se cumpla sin distinguir mayúsculas
por cualquier vía, y deja un historial auditable de sus cambios.

## Requisitos funcionales
Criterio común: todo guardado normal (aplicación, panel de administración, consola y código que
guarde el usuario a través del modelo) normaliza y valida cada regla. Además, la unicidad del correo
(RF-002) se garantiza también en cargas masivas y en escrituras directas a la base de datos; el
resto de reglas pueden no aplicarse en esas dos vías.

### RF-001 Correo normalizado
Cuando se cree o modifique un usuario, el sistema deberá guardar su correo sin espacios al
principio ni al final y en minúsculas (" Ana@X.com " → "ana@x.com"), sin alterar puntos ni
sufijos "+etiqueta".

### RF-002 Correo único sin distinguir mayúsculas
Si se intenta crear o modificar un usuario con un correo que, sin distinguir mayúsculas, coincide
con el de otro usuario (por ejemplo, "Ana@x.com" y "ana@x.com"), entonces el sistema deberá
rechazar la operación, incluso cuando el guardado no pase por la normalización de RF-001 (cargas
masivas o escritura directa) y aunque la otra cuenta esté inactiva (RF-007).

### RF-003 Nombre completo
El sistema deberá exigir a cada usuario un nombre completo, guardado sin espacios al principio ni
al final, no vacío, de 150 caracteres como máximo y en cualquier alfabeto. Si el nombre contiene
dos o más espacios seguidos, tabuladores, saltos de línea u otros caracteres de control, entonces
el sistema deberá rechazarlo.

### RF-004 Fecha de nacimiento
El sistema deberá exigir a cada usuario una fecha de nacimiento. Si la fecha es posterior al día
actual, o el día actual es anterior a la fecha en que el usuario cumple 18 años más 5 días,
entonces el sistema deberá rechazar la operación. Para quien nació un 29 de febrero, en un año no
bisiesto los 18 años se cumplen el 28 de febrero (puede registrarse desde el 5 de marzo).

### RF-005 País de residencia
El sistema deberá exigir a cada usuario un país de residencia como código ISO 3166-1 alpha-2
de la lista oficial vigente, guardado en mayúsculas ("es" → "ES"). Si el código no está en esa
lista (por ejemplo, "XX", o los de uso reservado como "XK" o "ZZ"), entonces el sistema deberá
rechazar la operación. Única excepción: el relleno "ZZ" de RF-011, que se conserva mientras no se
cambie el país.

### RF-006 Datos obligatorios para todas las cuentas
El sistema deberá exigir nombre, fecha de nacimiento y país a todas las cuentas, incluidas las de
staff y superusuario creadas por consola.

### RF-007 Estado de la cuenta
El sistema deberá crear cada cuenta como activa. Mientras una cuenta esté inactiva (borrado lógico),
el sistema deberá impedir que inicie sesión, excluirla de las consultas normales de usuarios y
conservar todos sus datos, incluido su correo, para poder reactivarla. El borrado físico queda
reservado a la administración. La verificación del correo es un dato independiente y no se
refleja en este estado.

### RF-008 Atributos de administración y alta
El sistema deberá registrar para cada usuario si pertenece al staff (por defecto, no), si es
superusuario (por defecto, no), la fecha de alta (asignada al crearse) y la fecha del último
inicio de sesión.

### RF-009 Historial de cambios
Cuando se cree, modifique o borre un usuario, el sistema deberá registrar una versión con todos sus
datos excepto la contraseña y la fecha del último inicio de sesión, junto con la fecha, el tipo de
cambio (alta, modificación o borrado) y quién lo hizo, si se conoce.

### RF-010 Conservación del historial
Cuando se borre físicamente un usuario, el sistema deberá conservar su historial.

### RF-011 Actualización de datos existentes
Cuando se aplique esta actualización sobre una base con cuentas existentes, el sistema deberá
conservar todas las cuentas y completar los datos nuevos con estos valores de relleno: nombre
"Usuario sin nombre", fecha de nacimiento 1900-01-01 y país "ZZ" (desconocido). Si
existen cuentas cuyos correos solo difieren en mayúsculas, entonces la actualización deberá fallar
indicándolo, sin fusionar ni borrar cuentas.

## Supuestos
- S-01 El modelo de usuario propio ya existe (feature `auth-headless`, primera migración aplicada);
  esta feature lo amplía, no lo sustituye.
- S-02 Las cuentas existentes son solo de desarrollo y de prueba; los valores de relleno de RF-011
  son reconocibles como tales y no representan datos reales.
- S-03 La edad se calcula con la fecha actual del servidor en el momento del alta o la
  modificación.
- S-04 La acción de desactivar la cuenta por su titular (el "RF-08" citado por el usuario) es de
  una feature futura; aquí solo se define qué implica estar inactiva (RF-007).
- S-05 El historial se conserva indefinidamente, también tras borrar la cuenta. *Riesgo:* guarda
  datos personales de exusuarios; si aplica una normativa con derecho de supresión, habrá que
  revisar esta decisión.
- S-06 El usuario aprobó usar `django-simple-history` como dependencia nueva para el historial
  (2026-09-29).
- S-07 Mientras no exista la feature de registro (D-01 del spike), el signup de allauth no podrá
  crear usuarios porque no pide nombre, fecha ni país; no habrá alta por la API.
- S-08 Los tests crean usuarios con una única función compartida que rellena valores válidos por
  defecto, y los tests del spike usan un adapter de test que completa nombre, fecha y país en el
  signup de allauth. Así, un campo obligatorio nuevo solo obliga a cambiar esos dos puntos (C-01).
- S-09 El historial empieza con esta feature: las cuentas existentes no reciben una entrada inicial,
  el relleno de RF-011 no se registra y, si no se sabe quién hizo un cambio (consola, migración),
  el autor queda vacío (C-05).
- S-10 La edad mínima de 18 años y 5 días es una regla de negocio propia. *Riesgo:* no coincide con
  ninguna mayoría de edad legal y habrá que poder justificarla.

## Fuera de alcance
- El resto de entidades del diagrama (registro pendiente, sesiones, consentimientos, términos,
  restablecimiento de contraseña, eventos de seguridad).
- El registro, las pantallas y la API de perfil.
- La acción de deshabilitar la cuenta por su titular.
- La política de retención y borrado del historial.
- Adaptar o desactivar el signup de allauth.

## Criterios de finalización
- CF-1 La migración se aplica sin errores sobre una base vacía y sobre una base con el usuario de
  prueba de `auth-headless`.
- CF-2 Un test demuestra que "Ana@x.com" y "ana@x.com" chocan, también cuando el segundo se guarda
  sin pasar por la normalización.
- CF-3 Hay tests para cada regla de RF-001…RF-008 y para el historial (RF-009, RF-010).
- CF-4 La suite `pytest` está en verde (incluidas `auth-headless` y el spike, que crean usuarios con
  los mecanismos de S-08), con cobertura ≥ 80 %, y `mypy`/`ruff`/`black` están limpios.

## Historial de cambios
- 2026-09-29 — Creación (feature nueva) — RF: RF-001…RF-011 — Estado: pendiente de clarificar
- 2026-09-29 — Clarificación (C-01…C-08) — RF: RF-002…RF-005, RF-007, RF-010, RF-011 ajustados;
  S-02, S-04 ajustados; S-08…S-10 añadidos — Estado: clarificado
- 2026-09-30 — Validación: cerrada con riesgo residual aceptado por el usuario (4 rondas;
  145 tests, cobertura 100 %; RF-001…RF-011 cubiertos). Superviviente aceptado: N13 (historial
  tras un guardado de last_login fallido) — Estado: cerrada
