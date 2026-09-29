# Spec: usuario-personalizado
Estado: borrador

## Objetivo (por qué)
El usuario del sistema ya existe como modelo propio (feature `auth-headless`), pero solo guarda el
correo. Esta feature le añade los datos personales que el dominio necesita (nombre, fecha de
nacimiento y país), hace que la regla "un correo, una cuenta" se cumpla sin distinguir mayúsculas
por cualquier vía, y deja un historial auditable de sus cambios.

## Requisitos funcionales
Criterio común: salvo que se diga lo contrario, cada regla se cumple por **cualquier vía** de alta
o modificación (aplicación, panel de administración, consola y código que guarde el usuario
directamente).

### RF-001 Correo normalizado
Cuando se cree o modifique un usuario, el sistema deberá guardar su correo sin espacios al
principio ni al final y en minúsculas (" Ana@X.com " → "ana@x.com"), sin alterar puntos ni
sufijos "+etiqueta".

### RF-002 Correo único sin distinguir mayúsculas
Si se intenta crear o modificar un usuario con un correo que, sin distinguir mayúsculas, coincide
con el de otro usuario (por ejemplo, "Ana@x.com" y "ana@x.com"), entonces el sistema deberá
rechazar la operación, incluso cuando el guardado no pase por la normalización de RF-001.

### RF-003 Nombre completo
El sistema deberá exigir a cada usuario un nombre completo, guardado sin espacios al principio ni
al final, no vacío, de 150 caracteres como máximo y en cualquier alfabeto.

### RF-004 Fecha de nacimiento
El sistema deberá exigir a cada usuario una fecha de nacimiento. Si la fecha es posterior al día
actual, o el usuario no ha cumplido 18 años en el día actual, entonces el sistema deberá rechazar
la operación.

### RF-005 País de residencia
El sistema deberá exigir a cada usuario un país de residencia como código ISO 3166-1 alpha-2
existente, guardado en mayúsculas ("es" → "ES"). Si el código no existe en la norma (por ejemplo,
"XX"), entonces el sistema deberá rechazar la operación.

### RF-006 Datos obligatorios para todas las cuentas
El sistema deberá exigir nombre, fecha de nacimiento y país a todas las cuentas, incluidas las de
staff y superusuario creadas por consola.

### RF-007 Estado de la cuenta
El sistema deberá crear cada cuenta como activa. Mientras una cuenta esté marcada como inactiva,
el sistema deberá tratarla como deshabilitada por su titular; la verificación del correo es un
dato independiente y no se refleja en este estado.

### RF-008 Atributos de administración y alta
El sistema deberá registrar para cada usuario si pertenece al staff (por defecto, no), si es
superusuario (por defecto, no), la fecha de alta (asignada al crearse) y la fecha del último
inicio de sesión.

### RF-009 Historial de cambios
Cuando se cree, modifique o borre un usuario, el sistema deberá registrar una versión con todos sus
datos excepto la contraseña y la fecha del último inicio de sesión, junto con la fecha, el tipo de
cambio (alta, modificación o borrado) y quién lo hizo, si se conoce.

### RF-010 Conservación del historial
Cuando se borre un usuario, el sistema deberá conservar su historial.

### RF-011 Actualización de datos existentes
Cuando se aplique esta actualización sobre una base con cuentas existentes, el sistema deberá
conservar todas las cuentas y completar los datos nuevos con valores de relleno válidos (S-02). Si
existen cuentas cuyos correos solo difieren en mayúsculas, entonces la actualización deberá fallar
indicándolo, sin fusionar ni borrar cuentas.

## Supuestos
- S-01 El modelo de usuario propio ya existe (feature `auth-headless`, primera migración aplicada);
  esta feature lo amplía, no lo sustituye.
- S-02 Las cuentas existentes son solo de desarrollo y de prueba; los valores de relleno serán
  válidos según RF-003…RF-005 y reconocibles como relleno (se concretan en la clarificación).
- S-03 La edad se calcula con la fecha actual del servidor en el momento del alta o la
  modificación.
- S-04 "Deshabilitada por su titular" es la semántica de `is_active` que usará una feature futura
  (el "RF-08" citado por el usuario); la acción de deshabilitar queda fuera de alcance.
- S-05 El historial se conserva indefinidamente, también tras borrar la cuenta. *Riesgo:* guarda
  datos personales de exusuarios; si aplica una normativa con derecho de supresión, habrá que
  revisar esta decisión.
- S-06 El usuario aprobó usar `django-simple-history` como dependencia nueva para el historial
  (2026-09-29).
- S-07 Mientras no exista la feature de registro (D-01 del spike), el signup de allauth no podrá
  crear usuarios porque no pide nombre, fecha ni país; no habrá alta por la API.

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
- CF-4 La suite `pytest` está en verde (incluidas `auth-headless` y el spike, adaptadas), con
  cobertura ≥ 80 %, y `mypy`/`ruff`/`black` están limpios.

## Historial de cambios
- 2026-09-29 — Creación (feature nueva) — RF: RF-001…RF-011 — Estado: pendiente de clarificar
