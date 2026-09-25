# Resumen — auth-headless
Estado: en progreso · Última actualización: 2026-09-25

> Las secciones "Qué se hizo" y "Cómo probarlo" se completan al terminar la feature.

## Marco teórico
Conceptos que surgieron durante esta feature, explicados de forma accesible para dejar
referencia.

### CSRF (Cross-Site Request Forgery) y por qué el cliente de token queda exento
**Qué es.** Un ataque donde un sitio malicioso engaña al **navegador** de la víctima para que
haga una petición a tu API **usando las cookies que el navegador adjunta automáticamente**. Como
el navegador manda la cookie de sesión sola en cada petición a tu dominio, un sitio de terceros
puede lanzar en segundo plano una acción autenticada (p. ej. un `POST`) y el servidor creería que
la hizo la víctima. Se abusa de la **autoridad ambiental** de la cookie.

**La defensa (token CSRF).** El backend exige, en las peticiones que cambian estado, un token
secreto que **solo tu propio frontend puede leer** (la *same-origin policy* impide que otro sitio
lo lea). Sin ese token, la petición se rechaza: así se demuestra que vino de tu app y no de un
tercero.

**Por qué el cliente de token (`X-Session-Token`) está exento.** No usa cookies: manda el token
en una **cabecera que el código del cliente pone explícitamente**. El navegador no la adjunta
sola, y un sitio de terceros no puede ponerla ni leerla para otro origen. No hay autoridad
ambiental que suplantar, así que CSRF no aplica.

**Regla mental:** CSRF protege lo que el navegador manda *automáticamente* (cookies). Lo que se
manda *manualmente* (una cabecera de token) no lo necesita. → Web (cookie) = con CSRF; escritorio
(token) = exento.

### IP real detrás del proxy (`X-Forwarded-For`)
**El problema.** En producción, delante de la app hay un **proxy inverso** (nginx, traefik…).
Quien abre la conexión con Django es el proxy, así que Django ve la **IP del proxy**, no la del
cliente. Para no perderla, el proxy la mete en la cabecera `X-Forwarded-For` (XFF).

**La cadena.** Con varios saltos, cada proxy **añade** una IP:
`X-Forwarded-For: <cliente>, <proxy1>, <proxy2>`.

**El peligro (suplantación).** El **cliente puede inventarse** esa cabecera antes de llegar a tu
proxy. Si tomas ingenuamente el valor de la izquierda, un atacante puede fingir cualquier IP
(burla listas blancas, envenena logs, evade límites por IP). La cabecera **no es de fiar por sí
sola**.

**La regla segura.** Solo se confía en las entradas que añade **tu propia infraestructura**. Con
**un único proxy de confianza** delante, ese proxy añade **al final (a la derecha)** la IP real
del que se conectó; todo lo de la izquierda pudo falsificarlo el cliente. → La IP real es la
**última entrada** de `X-Forwarded-For`. Si se añaden más saltos de confianza (p. ej. un CDN), la
posición se cuenta desde la derecha, por eso el número de proxies conviene dejarlo **configurable**.

## Qué se hizo
_(pendiente — se completa al terminar la feature)_

## Cómo probarlo (usuario)
_(pendiente — se completa al terminar la feature)_
