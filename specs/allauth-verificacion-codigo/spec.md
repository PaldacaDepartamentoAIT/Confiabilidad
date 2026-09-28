# Spec: allauth-verificacion-codigo
Estado: borrador
Tipo: spike (entregable: decisión D-01)

## Objetivo (por qué)
El registro definitivo seguirá este flujo: el usuario introduce sus datos, recibe un correo con un
código y un enlace, introduce el código y fija su contraseña. Si cierra la ventana tras validar el
código, puede reanudar desde el enlace sin volver a rellenar sus datos. El enlace lleva un
identificador opaco del registro pendiente, nunca la sesión.

Antes de diseñarlo hay que saber si django-allauth soporta dos condiciones de ese flujo:
- **Q1**: que el usuario no exista hasta verificar el correo.
- **Q2**: que el código no se consuma al validarlo.

La respuesta decide qué parte del registro va dentro de allauth y qué parte fuera (D-01).
Hipótesis de partida: el registro va fuera de allauth; el inicio de sesión y las sesiones, dentro.

## Requisitos funcionales
Criterio común: "allauth lo permite" significa que se consigue con settings documentados o
sobrescribiendo métodos públicos del adapter. Subclasear vistas o formularios internos, o
parchear la librería, cuenta como "no". Cada pregunta se responde por separado para el cliente
browser (cookie) y el cliente app (token).

### RF-001 Existencia del usuario durante el registro de allauth
Cuando se solicite un registro con verificación obligatoria del correo por código, el spike
deberá determinar, para cada cliente, si existe una fila de usuario antes de validar el código, y
dejar esa observación como un caso reproducible.

### RF-002 Código para un correo desconocido
Cuando se solicite un código de acceso para un correo sin usuario, el spike deberá determinar,
para cada cliente, si allauth emite un código y si validarlo permite crear el usuario en ese
momento, y dejarlo como un caso reproducible.

### RF-003 Reutilización del código en la misma sesión
Cuando un código ya se haya validado correctamente, el spike deberá determinar, para cada cliente,
si una segunda validación del mismo código en la misma sesión se acepta.

### RF-004 Validación desde otra sesión
Cuando el código se presente desde una sesión distinta de la que lo solicitó, tanto antes como
después de una primera validación, el spike deberá determinar, para cada cliente, si se acepta.

### RF-005 Entrada tardía en allauth
Cuando un usuario con el correo verificado se haya creado fuera del flujo de registro de allauth,
el spike deberá comprobar que ese usuario inicia sesión desde ambos clientes (cookie y token) y
que la consulta de sesión lo devuelve.

### RF-006 Decisión escrita
El spike deberá dejar por escrito la respuesta a Q1 y a Q2 (sí o no, por cliente, con la
evidencia que la respalda) y la decisión D-01 sobre qué parte del registro queda dentro de allauth.

### RF-007 Respuesta sin forzar la librería
Si una pregunta no puede resolverse afirmativamente con settings o con el adapter, entonces el
spike deberá responderla "no" con la evidencia reunida, sin recurrir a partes internas de allauth.

## Supuestos
- S-01 El código se consumirá al completar el registro (al fijar la contraseña), no al validarlo.
  Q2 pregunta si allauth permite eso. *Por qué:* reutilizarlo antes de completar el registro no
  añade riesgo, porque quien tiene acceso al correo ya tiene el enlace y el código. El código
  debe caducar.
- S-02 Las respuestas valen para la versión de allauth instalada al ejecutar el spike, y esa
  versión se registra junto a la decisión (el proyecto declara `>=65` sin fijarla).
- S-03 "No existe" significa que no hay ninguna fila en la tabla de usuarios. Una fila inactiva o
  sin verificar cuenta como que existe.
- S-04 El enlace de reanudación lleva un identificador opaco del registro pendiente, nunca la
  sesión ni el token de sesión.
- S-05 Los casos del spike se conservan como tests de caracterización: afirman el comportamiento
  observado, de modo que se detecte si un cambio de versión lo altera.
- S-06 La configuración de verificación que necesitan los experimentos no altera el
  comportamiento vigente de `auth-headless`, que tiene la verificación desactivada.

## Fuera de alcance
- Implementar el registro definitivo (registro pendiente, public id, pantallas).
- Envío real de correos.
- Interfaz de frontend.
- Rate limiting y la duración concreta de la caducidad del código.
- Fijar la versión de allauth (se propone aparte, porque es un cambio de dependencias).
- Proveedores sociales.

## Criterios de finalización
- CF-1 Q1 y Q2 tienen respuesta escrita por cliente, con evidencia (RF-001…RF-004, RF-007).
- CF-2 RF-005 verificado en ambos clientes.
- CF-3 La decisión D-01 está escrita en `resumen.md`.
- CF-4 La suite `pytest` está en verde con cobertura ≥ 80 %, `mypy`/`ruff`/`black` están limpios y
  el comportamiento de `auth-headless` sigue intacto.

## Historial de cambios
- 2026-09-28 — Creación (spike nuevo) — RF: RF-001…RF-007 — Estado: pendiente de clarificar
