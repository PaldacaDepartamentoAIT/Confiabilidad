# Spec: consentimientos
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
El sistema debe poder demostrar qué textos legales aceptó cada persona y cuándo: los términos de
uso y el consentimiento para comunicaciones de marketing. Esta feature guarda los documentos
versionados (editables desde el panel de administración mientras nadie los haya aceptado), registra
las aceptaciones de términos y las concesiones y revocaciones de marketing, y ofrece las
operaciones para que un usuario acepte, conceda o revoque. La prueba se conserva aunque se borre
la cuenta, identificada por una huella del correo que no se puede revertir sin un secreto del
servidor. El diagrama ER del usuario es la referencia
([ER](../procesos-pendientes/diagramas/er.png)), con las desviaciones de S-02.

## Requisitos funcionales
Criterio común: todo guardado normal (operaciones de esta feature, panel de administración,
consola y código que guarde a través del modelo) aplica cada regla. Las unicidades de RF-002 y
RF-011 se garantizan también en cargas masivas y en escrituras directas a la base de datos.

### RF-001 Documento legal
El sistema deberá guardar, para cada documento legal, su tipo (términos o marketing), su contenido,
su versión, su idioma, su fecha de alta (asignada al crearse) y una fecha de publicación opcional.
Si el contenido, la versión o el idioma están vacíos, entonces el sistema deberá rechazar el
guardado.

### RF-002 Versión única
Si se intenta guardar un documento con el mismo tipo, versión e idioma que otro, entonces el
sistema deberá rechazarlo.

### RF-003 Versión vigente
El sistema deberá considerar vigente, para cada tipo e idioma, el documento con la fecha de
publicación más reciente que no sea posterior al momento actual; a igual fecha, el creado más
tarde. Un documento sin fecha de publicación, o con fecha futura, es un borrador y no está vigente.
Si no hay ningún documento publicado para ese tipo e idioma, entonces no habrá versión vigente.

### RF-004 Gestión desde el panel de administración
El sistema deberá permitir al personal de administración crear, consultar y editar documentos de
ambos tipos (contenido, versión, idioma, tipo y fecha de publicación) desde el panel de
administración, y ver qué documentos tienen aceptaciones.

### RF-005 Documento aceptado inmutable
Si un documento ya tiene alguna aceptación de términos o algún consentimiento de marketing,
entonces el sistema deberá rechazar cualquier cambio de su contenido, versión, idioma o tipo, y su
borrado, también desde el panel de administración. Mientras no tenga ninguno, se podrá editar y
borrar libremente.

### RF-006 Aceptar términos
Cuando un usuario acepte los términos en un idioma, el sistema deberá registrar el usuario, el
documento de términos vigente en ese idioma, la huella de su correo (RF-012) y la fecha de
aceptación. Si no hay documento de términos vigente en ese idioma, o el documento indicado no es
el vigente, entonces el sistema deberá rechazar la aceptación sin registrar nada.

### RF-007 Aceptación repetida
Si un usuario acepta una versión de términos que ya tiene aceptada, entonces el sistema no deberá
registrar una aceptación nueva y deberá devolver la existente.

### RF-008 Conceder marketing
Cuando un usuario conceda el consentimiento de marketing en un idioma, el sistema deberá registrar
un consentimiento activo con el usuario, el documento de marketing vigente en ese idioma, la huella
de su correo (RF-012) y la fecha de concesión. Si no hay documento de marketing vigente en ese
idioma, o el indicado no es el vigente, entonces el sistema deberá rechazarlo sin registrar nada.

### RF-009 Concesión con un consentimiento activo
Si un usuario concede el consentimiento de marketing teniendo ya uno activo para el mismo
documento, entonces el sistema deberá devolver el existente sin registrar otro. Si el activo es
de otro documento, entonces deberá revocarlo (RF-010) y registrar el nuevo en una sola operación
(S-06).

### RF-010 Revocar marketing
Cuando un usuario revoque el consentimiento de marketing, el sistema deberá marcar su
consentimiento activo como no concedido y registrar la fecha de revocación, conservando la fila.
Si el usuario no tiene ningún consentimiento activo, entonces el sistema no deberá cambiar nada ni
dar error.

### RF-011 Un consentimiento de marketing activo por usuario
Si se intenta guardar un segundo consentimiento de marketing activo para el mismo usuario, entonces
el sistema deberá rechazarlo.

### RF-012 Huella del correo
Cuando se registre una aceptación de términos o una concesión de marketing, el sistema deberá
guardar una huella del correo del usuario normalizado (sin espacios al principio ni al final y en
minúsculas), calculada con un secreto del servidor, de forma que no se pueda recuperar el correo
sin ese secreto aunque se disponga de la base de datos, y que el mismo correo produzca siempre la
misma huella. La huella guardada no deberá cambiar aunque el usuario cambie después su correo.

### RF-013 Conservación al borrar la cuenta
Cuando se borre físicamente un usuario, el sistema deberá conservar sus aceptaciones de términos y
sus consentimientos de marketing, con el usuario vacío y la huella del correo intacta.

### RF-014 Cuenta inactiva
Si una cuenta inactiva intenta aceptar términos o conceder el consentimiento de marketing, entonces
el sistema deberá rechazarlo. La revocación del consentimiento de marketing deberá permitirse
siempre (S-07).

### RF-015 Estado de consentimiento de un usuario
El sistema deberá permitir consultar, para un usuario y un idioma, si ha aceptado los términos
vigentes y si tiene un consentimiento de marketing activo (y de qué documento).

### RF-016 Ejecución desde consola
El sistema deberá permitir desde consola, sin frontend ni API: ver el documento vigente de cada tipo
en un idioma, aceptar los términos, conceder y revocar el consentimiento de marketing, y consultar
el estado de RF-015, identificando al usuario por su correo.

## Supuestos
- S-01 Las operaciones se exponen como funciones del backend y órdenes de consola (RF-016). La API,
  las pantallas y la integración con el registro quedan fuera (pregunta 8). La API futura
  reutilizará las mismas operaciones.
- S-02 Desviaciones respecto al diagrama ER, decididas en la entrevista: el documento gana un tipo
  (términos o marketing; pregunta 2) y una fecha de publicación (pregunta 4); el consentimiento de
  marketing apunta al documento de marketing aceptado; la fecha de revocación es opcional (el
  diagrama la marca obligatoria, lo que impide un consentimiento activo) y la fecha de aceptación de
  términos es obligatoria (el diagrama la deja opcional). El usuario es opcional y se vacía al
  borrar la cuenta en ambas tablas, como en el diagrama.
- S-03 `terms_version` y `marketing_opt_in` del registro pendiente (S-03 de `procesos-pendientes`)
  no se añaden aquí (pregunta 1): pasan a una feature futura que una el registro con los
  consentimientos.
- S-04 El idioma es uno de los configurados en el sistema. No hay idioma de reserva: si no existe
  versión vigente en el idioma pedido, la operación se rechaza (RF-006, RF-008).
- S-05 La fecha de publicación se puede cambiar aunque el documento tenga aceptaciones (RF-005 solo
  bloquea contenido, versión, idioma, tipo y borrado). *Riesgo:* quitarle la fecha a un documento
  aceptado lo vuelve borrador con aceptaciones; se revisará en la clarificación.
- S-06 Conceder marketing con un consentimiento activo de otra versión revoca el anterior y crea uno
  nuevo (RF-009), para que el historial muestre qué texto rige en cada momento.
- S-07 Una cuenta inactiva no puede aceptar ni conceder (RF-014), pero sí revocar: retirar el
  consentimiento no debe depender del estado de la cuenta.
- S-08 La aceptación de términos no caduca ni se revoca en esta feature. Exigir aceptar de nuevo al
  publicar una versión nueva es decisión del flujo de la aplicación (RF-015 da el dato).
- S-09 El secreto de la huella del correo no rota en esta feature. *Riesgo:* si se cambia, las
  huellas antiguas dejan de coincidir con las nuevas para el mismo correo.
- S-10 La inmutabilidad de RF-005 se aplica en los guardados normales y en el panel de
  administración; no se garantiza en cargas masivas ni en escrituras directas a la base de datos.

## Fuera de alcance
- API, pantallas y textos mostrados al usuario final (S-01).
- Integración con el registro pendiente y con el alta de la cuenta (S-03).
- Buscar aceptaciones a partir de un correo (la huella lo permite, pero la consulta es de otra
  feature).
- Rotación del secreto de la huella (S-09).
- Envío de comunicaciones de marketing y gestión de listas.
- El resto de tablas del diagrama ER (UserSession, SecurityEvent, PasswordResetRequest).

## Criterios de finalización
- CF-1 Las migraciones se aplican sin errores sobre la base de `procesos-pendientes`, con la
  unicidad de RF-002 y RF-011 garantizada por la base de datos.
- CF-2 Desde el panel de administración se crean, editan y publican documentos de términos y de
  marketing, y un documento con aceptaciones no deja cambiar su contenido ni borrarse.
- CF-3 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-4 Aceptar términos, conceder y revocar marketing y consultar el estado se pueden hacer solo con
  las órdenes de RF-016, y los pasos están documentados en `resumen.md`.

## Historial de cambios
- 2026-10-07 — Creación (feature nueva) — RF: RF-001…RF-016 — Estado: pendiente de clarificar
