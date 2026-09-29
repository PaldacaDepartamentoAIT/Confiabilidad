# Spec: allauth-verificacion-codigo
Estado: aprobada
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
Diseño previsto para el registro definitivo (S-10): los datos de quien se registra se guardan en
un registro pendiente propio, y solo al fijar la contraseña, tras confirmar el código, se crea la
fila en la tabla de usuarios.

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
Cuando se solicite un código de acceso para un correo sin usuario, con la protección contra la
enumeración de cuentas activa (misma respuesta exista o no el usuario), el spike deberá
determinar, para cada cliente, si allauth emite un código real (que llega al buzón de salida) y
si validarlo permite crear el usuario en ese momento, y dejarlo como un caso reproducible. Una
respuesta de "enviado" sin código en el buzón cuenta como que no emite código.

### RF-003 Reutilización del código en la misma sesión
Cuando un código ya se haya validado correctamente, el spike deberá determinar, para cada cliente,
si se acepta una segunda validación del mismo código en la misma sesión.

### RF-004 Validación desde otra sesión
Cuando el código se presente desde una sesión distinta de la que lo solicitó, tanto antes como
después de una primera validación, el spike deberá determinar, para cada cliente, si se acepta.
RF-004 es el único requisito que responde al caso "desde otra sesión" de Q2.

### RF-005 Entrada tardía en allauth
Mientras la verificación obligatoria del correo esté activa, cuando se fije la contraseña de un
registro pendiente guardado fuera de allauth, con su código ya confirmado, y sus datos se
conviertan a través de allauth en un usuario con el correo marcado como verificado, el spike
deberá comprobar que ese usuario inicia sesión desde ambos clientes (cookie y token) y que la
consulta de sesión lo devuelve. "A través de allauth" significa usar su adapter o los gestores de
sus modelos públicos (RF-007), sin escribir directamente en sus tablas.

### RF-006 Decisión escrita
El spike deberá dejar por escrito la respuesta a Q1 y a Q2 (sí o no, por cliente, con la
evidencia que la respalda) y la decisión D-01 sobre qué parte del registro queda dentro de allauth.
Si una pregunta funciona en un cliente y no en el otro, se buscará una alternativa rápida (dentro
del criterio común) que funcione en ambos. Si no la hay, la respuesta será "no", indicando en qué
cliente funcionó y en cuál no.

### RF-007 Respuesta sin forzar la librería
Si una pregunta no puede resolverse afirmativamente con settings o con el adapter, entonces el
spike deberá responderla "no" con la evidencia reunida, sin recurrir a partes internas de allauth.
Cada "no" irá acompañado de la lista de settings y métodos del adapter probados, y el código del
spike solo importará de allauth su adapter, sus settings y sus modelos públicos
(`allauth.account.models`), nunca vistas, formularios ni módulos internos. Como excepción, podrá
incluir o recargar el módulo de URLs de allauth headless (`allauth.headless.urls`), que es el
punto de integración documentado que ya usa `config/urls.py`, para que existan las rutas que
dependen de settings (RF-002). Todo ello se comprueba en la revisión, contando también los
imports hechos por texto (por ejemplo, con `importlib`).

### RF-008 Reenvío del código
Cuando se solicite de nuevo el código para una verificación pendiente, el spike deberá
determinar, para cada cliente, si el código anterior deja de aceptarse y si se emite uno nuevo.

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
- S-07 Los tests de caracterización no son funcionalidad, así que no siguen la secuencia de P-04
  (test que falla → implementación). Cualquier código de producción sí la sigue.
- S-08 El código de configuración o adapter que necesite el spike vive en los tests. Solo pasa a
  producción si D-01 lo adopta, con su propio ciclo TDD y con la suite de `auth-headless` en
  verde.
- S-09 En el registro definitivo, pedir el código de nuevo invalida el anterior y envía uno nuevo
  por correo. Los enlaces enviados siguen funcionando hasta que caducan, porque pertenecen al
  registro pendiente propio (S-04), no a allauth.
- S-10 El registro definitivo usará un registro pendiente propio, fuera de allauth: guarda los
  datos y el hecho de que el código se confirmó, y al fijar la contraseña crea el usuario a
  través de allauth con su correo marcado como verificado. En el spike ese registro pendiente solo se simula dentro de los tests (S-08); su
  implementación real es otra feature.

## Fuera de alcance
- Implementar el registro definitivo (registro pendiente, public id, pantallas).
- Envío real de correos.
- Interfaz de frontend.
- Rate limiting y la duración concreta de la caducidad del código.
- Fijar la versión de allauth (se propone aparte, porque es un cambio de dependencias).
- Proveedores sociales.

## Criterios de finalización
- CF-1 Q1 y Q2 tienen respuesta escrita por cliente, con evidencia (RF-001…RF-004, RF-007,
  RF-008).
- CF-2 RF-005 verificado en ambos clientes.
- CF-3 La decisión D-01 está escrita en `resumen.md`.
- CF-4 La suite `pytest` está en verde con cobertura ≥ 80 %, `mypy`/`ruff`/`black` están limpios y
  el comportamiento de `auth-headless` sigue intacto.

## Historial de cambios
- 2026-09-28 — Creación (spike nuevo) — RF: RF-001…RF-007 — Estado: pendiente de clarificar
- 2026-09-28 — Clarificación (C-01…C-08) — RF: RF-002…RF-007 ajustados; RF-008 añadido;
  S-07…S-09 añadidos — Estado: clarificado
- 2026-09-28 — Cambio: diseño previsto del registro pendiente; entrada tardía desde un registro
  pendiente; modelos públicos permitidos — RF: RF-005, RF-007 — Estado: clarificado
- 2026-09-28 — Clarificación (C-09…C-11): el usuario se crea al fijar la contraseña; la
  conversión pasa por allauth — RF: RF-005 ajustado; S-10 ajustado — Estado: clarificado
- 2026-09-29 — Cambio (origen: validación NO CUMPLIDA): excepción para incluir o recargar
  `allauth.headless.urls`; la revisión de imports incluye los hechos por texto — RF: RF-007 —
  Estado: clarificado
