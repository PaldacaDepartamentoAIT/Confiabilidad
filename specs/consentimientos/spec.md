# Spec: consentimientos
Estado: aprobada
Aprobación: ligera

## Objetivo (por qué)
El sistema debe poder demostrar qué textos legales aceptó cada persona y cuándo: los términos de
uso y el consentimiento para comunicaciones de marketing. Esta feature guarda los documentos
versionados en español, portugués de Brasil e inglés (editables desde el panel de administración
mientras nadie los haya aceptado), registra las aceptaciones de términos y las concesiones y
revocaciones de marketing, y ofrece las operaciones para que un usuario acepte, conceda o revoque.
La prueba se conserva aunque se borre la cuenta, identificada por una huella del correo que no se
puede revertir sin un secreto del servidor, y cada alta, cambio o borrado queda en un historial
con su autor. El diagrama ER del usuario es la referencia
([ER](../procesos-pendientes/diagramas/er.png)), con las desviaciones de S-02.

## Requisitos funcionales
Criterio común: todo guardado normal (operaciones de esta feature, panel de administración,
consola y código que guarde a través del modelo) aplica cada regla. Las unicidades de RF-002,
RF-007 y RF-011 se garantizan también en cargas masivas y en escrituras directas a la base de
datos.

### RF-001 Documento legal
El sistema deberá guardar, para cada documento legal, su tipo (términos o marketing), su contenido
en Markdown, su versión, su idioma, si exige una nueva aceptación (solo en los de términos), su
fecha de alta (asignada al crearse) y una fecha de publicación opcional. Si el contenido está vacío
o contiene etiquetas HTML, si la versión no tiene entre 1 y 20 caracteres formados solo por letras,
dígitos, puntos y guiones, o si el idioma no es español (`es`), portugués de Brasil (`pt-BR`) o
inglés (`en`), entonces el sistema deberá rechazar el guardado.

### RF-002 Versión única
Si se intenta guardar un documento con el mismo tipo e idioma que otro y una versión que solo
difiere de la suya en mayúsculas o minúsculas ("V1" y "v1") o es igual, entonces el sistema deberá
rechazarlo.

### RF-003 Versión vigente
El sistema deberá considerar que una versión de un tipo entra en vigor cuando sus documentos en los
tres idiomas están publicados, en la fecha de publicación más tardía de los tres. La versión
vigente de cada tipo es la que entró en vigor más recientemente sin que esa fecha sea posterior al
momento actual; a igual fecha, aquella cuyo documento más reciente se creó más tarde. Un documento
sin fecha de publicación, o con fecha futura, es un borrador. Si a una versión le falta algún idioma
o alguno es borrador, entonces esa versión no estará en vigor; si ninguna lo está, entonces no habrá
versión vigente de ese tipo.

### RF-004 Gestión de documentos desde el panel de administración
El sistema deberá permitir a los miembros del staff con los permisos correspondientes crear,
consultar, editar y borrar documentos de ambos tipos desde el panel de administración, con las
restricciones de RF-005, y ver qué documentos tienen aceptaciones. Si un miembro del staff sin esos
permisos intenta hacerlo, entonces el sistema deberá impedirlo.

### RF-005 Versión aceptada inmutable
Si algún documento de una versión tiene alguna aceptación de términos o algún consentimiento de
marketing (revocados incluidos), entonces el sistema deberá rechazar, en todos los documentos de esa
versión, cualquier cambio de su contenido, versión, idioma, tipo, fecha de publicación o exigencia
de nueva aceptación, y su borrado. Mientras ningún documento de la versión los tenga, se podrán
editar y borrar libremente.

### RF-006 Aceptar términos
Cuando un usuario acepte un documento de términos concreto (el que se le mostró, identificado por su
versión e idioma), el sistema deberá registrar el usuario, ese documento, la huella de su correo
(RF-012) y la fecha de aceptación. Si el documento no existe, no es de términos o no pertenece a la
versión vigente, entonces el sistema deberá rechazar la aceptación sin registrar nada.

### RF-007 Aceptación repetida
Si un usuario acepta un documento de términos del que ya tiene una aceptación no revocada, entonces
el sistema no deberá registrar una nueva y deberá devolver la existente. El sistema no deberá
permitir dos aceptaciones no revocadas del mismo usuario y documento.

### RF-008 Conceder marketing
Cuando un usuario conceda el consentimiento de marketing sobre un documento de marketing concreto
(el que se le mostró, identificado por su versión e idioma), el sistema deberá registrar un
consentimiento activo con el usuario, ese documento, la huella de su correo (RF-012) y la fecha de
concesión. Si el documento no existe, no es de marketing o no pertenece a la versión vigente,
entonces el sistema deberá rechazarlo sin registrar nada.

### RF-009 Concesión con un consentimiento activo
Si un usuario concede el consentimiento de marketing teniendo ya uno activo para el mismo
documento, entonces el sistema deberá devolver el existente sin registrar otro. Si el activo es
de otro documento, entonces deberá sustituirlo: revocarlo (RF-010) y registrar el nuevo en una
sola operación.

### RF-010 Revocar marketing
Cuando un usuario revoque el consentimiento de marketing, o soporte técnico lo deshabilite desde el
panel (RF-019), el sistema deberá marcar el consentimiento activo como no concedido y registrar la
fecha de revocación, conservando la fila. Si el usuario no tiene ningún consentimiento activo,
entonces el sistema no deberá cambiar nada ni dar error.

### RF-011 Un consentimiento de marketing activo por usuario
Si se intenta guardar un segundo consentimiento de marketing activo para el mismo usuario, entonces
el sistema deberá rechazarlo.

### RF-012 Huella del correo
Cuando se registre una aceptación de términos o un consentimiento de marketing, el sistema deberá
calcular y guardar una huella del correo del usuario normalizado (sin espacios al principio ni al
final y en minúsculas), con un secreto del servidor, de forma que no se pueda recuperar el correo
sin ese secreto aunque se disponga de la base de datos, y que el mismo correo produzca siempre la
misma huella. La huella se calcula solo al crear la fila, nunca se introduce a mano y no se podrá
modificar después por ninguna vía (tampoco desde el panel), aunque el usuario cambie su correo. Si
se intenta crear una fila sin usuario, entonces el sistema deberá rechazarla. Si se intenta asignar
otro usuario a una fila existente, entonces el sistema deberá rechazarlo, también si la fila ya no
tiene usuario; solo se permite vaciarlo, y la huella se conserva.

### RF-013 Conservación al borrar la cuenta
Cuando se borre físicamente un usuario, el sistema deberá conservar sus aceptaciones de términos y
sus consentimientos de marketing con el usuario vacío, la huella del correo intacta y su estado sin
cambios: un consentimiento de marketing activo sigue activo (S-11).

### RF-014 Cuenta inactiva
Si una cuenta inactiva intenta aceptar términos o conceder el consentimiento de marketing, entonces
el sistema deberá rechazarlo. La revocación del consentimiento de marketing deberá permitirse
siempre. Esta regla no se aplica a lo que haga soporte técnico desde el panel (RF-019).

### RF-015 Estado de consentimiento de un usuario
El sistema deberá permitir consultar, para un usuario:
- si tiene los términos aceptados: es así cuando tiene una aceptación no revocada de un documento,
  en cualquier idioma, cuya versión entró en vigor en la misma fecha o después que la versión en
  vigor más reciente que exige nueva aceptación;
- si tiene un consentimiento de marketing activo, y de qué documento.

Si no hay versión vigente de términos, entonces la consulta deberá indicarlo en lugar de responder
sí o no.

### RF-016 Ejecución desde consola
El sistema deberá permitir desde consola, sin frontend ni API: ver el documento vigente de cada tipo
en un idioma, aceptar un documento de términos, conceder (sobre un documento de marketing) y revocar
el consentimiento de marketing, y consultar el estado de RF-015, identificando al usuario por su
correo y el documento por su tipo, versión e idioma.

### RF-017 Exigencia de nueva aceptación coherente
Si un documento de términos indica si exige nueva aceptación con un valor distinto del de otro
documento de su misma versión, entonces el sistema deberá rechazar el guardado. La primera versión
de términos que entre en vigor deberá considerarse siempre una versión que exige aceptación.

### RF-018 Revocar una aceptación de términos
Cuando soporte técnico deshabilite una aceptación de términos desde el panel (RF-019), el sistema
deberá registrar su fecha de revocación, conservar la fila y dejar de tenerla en cuenta para RF-007
y RF-015.

### RF-019 Gestión de aceptaciones y consentimientos por soporte técnico
El sistema deberá crear un grupo «Soporte técnico» cuyos miembros puedan ver, crear, editar,
deshabilitar (RF-010, RF-018) y borrar aceptaciones de términos y consentimientos de marketing desde
el panel de administración. Al crear o editar se aplican las unicidades (RF-007, RF-011) y la huella
automática e inmutable (RF-012), pero se permiten documentos de versiones no vigentes y cuentas
inactivas. Si un miembro del staff que no pertenece al grupo ni es superusuario intenta hacerlo,
entonces el sistema deberá impedirlo.

### RF-020 Historial de cambios
Cuando se cree, modifique o borre un documento, una aceptación de términos o un consentimiento de
marketing, el sistema deberá registrar una versión con todos sus datos, la fecha, el tipo de cambio
(alta, modificación o borrado) y quién lo hizo, si se conoce. En el historial de aceptaciones y
consentimientos no se deberá guardar el usuario de la fila, y solo se registrará como autor a un
miembro del staff distinto de ese usuario; si el autor es el propio usuario de la fila, la versión
quedará sin autor. Así, una vez borrada la cuenta, ningún dato directo (la huella no cuenta)
permite asociar la prueba a la persona. El vaciado del usuario al borrar la cuenta no genera
versión. El historial se deberá conservar tras el borrado y no se podrá modificar desde el panel
de administración.

## Supuestos
- S-01 Las operaciones se exponen como funciones del backend y órdenes de consola (RF-016). La API,
  las pantallas y la integración con el registro quedan fuera (pregunta 8). La API futura
  reutilizará las mismas operaciones.
- S-02 Desviaciones respecto al diagrama ER, decididas en la entrevista y la clarificación: el
  documento gana un tipo (términos o marketing; pregunta 2), una fecha de publicación (pregunta 4)
  y la exigencia de nueva aceptación (C-05); la aceptación de términos gana una fecha de revocación
  opcional (C-02); el consentimiento de marketing apunta al documento aceptado; su fecha de
  revocación es opcional (el diagrama la marca obligatoria, lo que impide un consentimiento activo)
  y la fecha de aceptación de términos es obligatoria (el diagrama la deja opcional). El usuario es
  opcional y se vacía al borrar la cuenta en ambas tablas, como en el diagrama.
- S-03 `terms_version` y `marketing_opt_in` del registro pendiente (S-03 de `procesos-pendientes`)
  no se añaden aquí (pregunta 1): pasan a una feature futura que una el registro con los
  consentimientos.
- S-04 Los idiomas son español, portugués de Brasil e inglés (C-03). El idioma de una aceptación es
  el del documento aceptado; no hay idioma de reserva para mostrar el vigente.
- S-05 Soporte técnico puede crear, editar y borrar pruebas de consentimiento (C-02). *Riesgo:* el
  historial (RF-020) deja constancia de quién lo hizo, pero no lo impide; la prueba vale lo que
  valga la confianza en ese grupo.
- S-06 Una versión de cada tipo se publica a la vez en los tres idiomas (C-10): no hay vigentes
  distintas por idioma, y una aceptación en un idioma vale para todos (C-05).
- S-07 Una cuenta inactiva no puede aceptar ni conceder (RF-014), pero sí revocar: retirar el
  consentimiento no debe depender del estado de la cuenta.
- S-08 Una aceptación de términos no caduca con el tiempo: deja de valer cuando entra en vigor una
  versión que exige nueva aceptación (RF-015) o cuando soporte la revoca (RF-018). Exigir que el
  usuario acepte en ese momento es decisión del flujo de la aplicación (RF-015 da el dato). Una
  versión menor (por ejemplo, una errata) puede publicarse sin exigirla.
- S-09 El secreto de la huella del correo no rota en esta feature. *Riesgo:* si se cambia, las
  huellas antiguas dejan de coincidir con las nuevas para el mismo correo.
- S-10 La inmutabilidad de RF-005 y la coherencia de RF-017 se aplican en los guardados normales y
  en el panel; no se garantizan en cargas masivas ni en escrituras directas a la base de datos.
- S-11 Un consentimiento de marketing activo sigue activo al borrar la cuenta (C-06), porque queda
  ligado a la huella del correo. *Riesgo:* la persona ya no puede revocarlo por sí misma (solo
  soporte), y si vuelve a registrarse con el mismo correo puede tener dos consentimientos activos
  con la misma huella, uno sin usuario.
- S-12 Los superusuarios tienen los mismos permisos que el grupo «Soporte técnico» y que el staff
  con permisos de documentos.
- S-13 El historial reutiliza la dependencia de historial ya aprobada en `usuario-personalizado`
  (S-06 de esa feature); no añade dependencias nuevas.
- S-14 El contenido se escribe en Markdown sin HTML (C-07): quien lo muestre deberá tratar el texto
  como Markdown y no interpretar HTML.
- S-15 Hallazgo H-1 de la validación (2026-10-08): el historial del usuario (`usuario-personalizado`)
  guarda su correo en claro, también tras borrar la cuenta. Para que no se pueda llegar a él desde
  las pruebas de consentimiento, el historial de aceptaciones y consentimientos no guarda el usuario
  ni lo registra como autor (RF-020), y la huella es inmutable (RF-012). «Dato directo» es una
  referencia a la persona (su usuario o su identificador); las fechas no lo son (C-13). *Riesgo
  residual:* la fila viva conserva el usuario mientras la cuenta existe, y las fechas de aceptación
  podrían cruzarse con las del historial del usuario; el correo de las cuentas borradas sigue en el
  historial del usuario, cuya retención es de otra feature.

## Fuera de alcance
- API, pantallas y textos mostrados al usuario final (S-01).
- Integración con el registro pendiente y con el alta de la cuenta (S-03).
- Que el propio usuario revoque su aceptación de términos (solo soporte, RF-018).
- Buscar aceptaciones a partir de un correo (la huella lo permite, pero la consulta es de otra
  feature).
- Rotación del secreto de la huella (S-09).
- Envío de comunicaciones de marketing y gestión de listas.
- El resto de tablas del diagrama ER (UserSession, SecurityEvent, PasswordResetRequest).

## Criterios de finalización
- CF-1 Las migraciones se aplican sin errores sobre la base de `procesos-pendientes`, con las
  unicidades de RF-002, RF-007 y RF-011 garantizadas por la base de datos, y crean el grupo
  «Soporte técnico».
- CF-2 Desde el panel de administración, el staff con permisos crea, edita y publica documentos de
  términos y de marketing en los tres idiomas, y una versión con aceptaciones no deja cambiar ni
  borrar ninguno de sus documentos.
- CF-3 Desde el panel, un miembro de «Soporte técnico» ve, crea, edita, deshabilita y borra
  aceptaciones y consentimientos, el resto del staff no puede, y el historial muestra quién hizo
  cada cambio.
- CF-4 Hay tests para cada RF; la suite `pytest` está en verde con cobertura ≥ 80 % y
  `mypy`/`ruff`/`black` están limpios.
- CF-5 Aceptar términos, conceder y revocar marketing y consultar el estado se pueden hacer solo con
  las órdenes de RF-016, y los pasos están documentados en `resumen.md`.

## Historial de cambios
- 2026-10-07 — Creación (feature nueva) — RF: RF-001…RF-016 — Estado: pendiente de clarificar
- 2026-10-07 — Clarificación (C-01…C-11) — RF: RF-001…RF-010, RF-012…RF-016 ajustados;
  RF-017…RF-020 añadidos; S-02, S-04…S-08 ajustados; S-11…S-14 añadidos — Estado: clarificado
- 2026-10-08 — Cambio por el hallazgo H-1 de la validación: huella inmutable, sin cambiar el
  usuario de una fila; el historial de aceptaciones y consentimientos no guarda el usuario ni lo
  registra como autor — RF: RF-012, RF-019, RF-020; S-15 añadido — Estado: clarificado
- 2026-10-08 — Clarificación del cambio (C-12…C-16): nunca el propio usuario como autor; tampoco se
  asigna usuario a una fila sin él; el vaciado por borrado de la cuenta no genera versión (descarta
  la corrección T-026); los usuarios ya guardados en el historial se eliminan — RF: RF-012, RF-020
  ajustados; S-15 ajustado — Estado: clarificado
