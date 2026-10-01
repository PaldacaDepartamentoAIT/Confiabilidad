# Spec: procesos-pendientes
Estado: borrador

## Objetivo (por qué)
El registro y el cambio de contraseña exigen demostrar acceso al correo con un código antes de
crear la cuenta o cambiar la clave. Esta feature guarda esos procesos en curso y aplica sus reglas
(código de un solo uso con caducidad, límite de intentos, un proceso por correo o cuenta), para
que las futuras features de registro y de cambio de contraseña solo tengan que usarlos. Los
diagramas aportados por el usuario son la referencia:
[ER](diagramas/er.png), [flujo de registro](diagramas/flujo-registro.png) y
[flujo de cambio de contraseña](diagramas/flujo-cambio-contrasena.png).

## Requisitos funcionales
### RF-001 Registro pendiente
El sistema deberá guardar, para cada registro pendiente, el correo, el nombre completo, la fecha de
nacimiento, el país, un identificador público, la huella del código vigente, su caducidad, el
número de intentos fallidos, si el código ya se confirmó (y cuándo) y la fecha de alta.

### RF-002 Datos del registro pendiente válidos
Cuando se guarde un registro pendiente, el sistema deberá normalizar y validar correo, nombre,
fecha de nacimiento y país con las mismas reglas que la cuenta de usuario (RF-001 y RF-003…RF-005
de `usuario-personalizado`) y rechazar el guardado si alguno no es válido.

### RF-003 Un registro pendiente por correo
Si se intenta guardar un registro pendiente cuyo correo coincide, sin distinguir mayúsculas, con
el de otro registro pendiente, entonces el sistema deberá rechazarlo, también en cargas masivas y
escrituras directas a la base de datos.

### RF-004 Correo con cuenta
Si el correo de un registro pendiente coincide, sin distinguir mayúsculas, con el de una cuenta
existente (activa o no), entonces el sistema no deberá guardar el registro pendiente.

### RF-005 Registro repetido
Cuando se solicite un registro para un correo que ya tiene un registro pendiente vigente, el
sistema deberá conservar los datos existentes, descartar los nuevos, asignar un identificador
público nuevo, emitir un código nuevo, poner los intentos a 0 y anular la confirmación (S-06).

### RF-006 Solicitud de cambio de contraseña
El sistema deberá guardar, para cada solicitud de cambio de contraseña, la cuenta a la que
pertenece, un identificador público, la huella del código vigente, su caducidad, los intentos
fallidos, si el código ya se confirmó (y cuándo) y la fecha de alta, con un máximo de una
solicitud por cuenta. Cuando se solicite otra para la misma cuenta, el sistema deberá
reemplazarla: identificador público nuevo, código nuevo, intentos a 0 y sin confirmar.

### RF-007 Identificador público
El sistema deberá asignar a cada proceso un identificador público aleatorio, imposible de deducir
del correo o de la cuenta, y único entre los procesos de su tipo.

### RF-008 Código
Cuando se emita un código, el sistema deberá generar uno de 6 dígitos, vigente 15 minutos,
entregarlo una sola vez para su envío y guardar solo una huella que no permita recuperarlo sin un
secreto del servidor, aunque se disponga de la base de datos.

### RF-009 Verificación del código
Cuando se presente un código para un proceso, el sistema deberá aceptarlo solo si coincide, no ha
caducado y no se han agotado los intentos, y al aceptarlo deberá marcar el proceso como
confirmado. Si el código no coincide, entonces el sistema deberá sumar un intento fallido.

### RF-010 Bloqueo por intentos
Si un proceso acumula 5 intentos fallidos, entonces el sistema deberá rechazar cualquier código
posterior, incluso el correcto, hasta que se emita uno nuevo, que reinicia los intentos.

### RF-011 Caducidad del proceso
Un proceso caduca 15 minutos después de que caduque su código vigente. Mientras un proceso esté
caducado, el sistema deberá tratarlo como inexistente: no aceptará códigos, no permitirá
completarlo y no lo tendrá en cuenta para RF-003 ni para RF-005.

### RF-012 Fin del proceso
Cuando un proceso confirmado se complete, el sistema deberá borrarlo. Si se intenta completar un
proceso sin confirmar o caducado, entonces el sistema deberá rechazarlo.

### RF-013 Limpieza
El sistema deberá permitir borrar desde consola todos los procesos caducados, informando de
cuántos borró.

### RF-014 Borrado de cuenta
Cuando se borre físicamente una cuenta, el sistema deberá borrar su solicitud de cambio de
contraseña.

## Supuestos
- S-01 Esta feature no incluye flujos: API, pantallas, envío de correos, mensajes neutros,
  redirecciones (ni el identificador sin proceso detrás para cuentas existentes), el aviso
  "ya tienes cuenta", el límite de frecuencia del reenvío ni el cierre de sesiones tras cambiar la
  contraseña. Son de las features de registro y de cambio de contraseña, que usarán estas
  operaciones.
- S-02 Los diagramas del usuario (ER, flujo de registro y flujo de cambio de contraseña, recibidos
  el 2026-10-01) son la referencia y se guardan en `specs/procesos-pendientes/diagramas/`.
- S-03 Términos y marketing (`terms_version`, `marketing_opt_in`) se añadirán en la feature de
  consentimientos, junto con su tabla de términos (C-07).
- S-04 La gracia de 15 minutos tras caducar el código (diagrama de registro) se aplica igual al
  cambio de contraseña, para permitir fijar la clave tras confirmar el código y cerrar la ventana.
- S-05 Quien complete el proceso (crear la cuenta o cambiar la clave) será la feature del flujo;
  aquí solo se exige que el proceso esté confirmado y vigente y que se borre al completarse.
- S-06 **Pendiente de confirmar.** Repetir el registro con un correo que tiene un registro
  pendiente cambia su identificador público y anula la confirmación (RF-005). *Por qué:* si el
  identificador existente se entregara a quien repite el formulario, un tercero podría fijar la
  contraseña de un registro ya confirmado o agotar sus intentos. *Coste:* el enlace anterior deja
  de valer y hay que usar el último correo.
- S-07 Un código de 6 dígitos con 5 intentos por código: el freno real a la fuerza bruta es el
  límite de frecuencia del reenvío (S-01), que fija la feature de flujo.

## Fuera de alcance
- Flujos de registro y de cambio de contraseña (ver S-01).
- Términos, marketing y el resto de tablas del diagrama ER (MarketingConsent, Terms, UserTerms,
  UserSession, SecurityEvent).
- Programar la limpieza periódica (RF-013 solo ofrece la orden).
- Histórico de solicitudes: los procesos terminados o caducados no se conservan.

## Criterios de finalización
- CF-1 Las migraciones se aplican sobre la base de `usuario-personalizado`, con unicidad
  garantizada por la base de datos en el identificador público de cada tipo de proceso, en el
  correo del registro pendiente (sin distinguir mayúsculas) y en la cuenta de la solicitud de
  cambio de contraseña.
- CF-2 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-3 Los diagramas están guardados en `specs/procesos-pendientes/diagramas/` y enlazados desde
  la spec.

## Historial de cambios
- 2026-10-01 — Creación (feature nueva) — RF: RF-001…RF-014 — Estado: pendiente de clarificar
