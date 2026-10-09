# Resumen — auth-headless
Estado: validada (CUMPLIDA) · Última actualización: 2026-09-25

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

### Configuración gateada por variables de entorno (env-var gating)
**Qué es.** "Gatear por variable de entorno" es hacer que un comportamiento se active o desactive
según el valor de una variable de entorno, en vez de dejarlo fijo en el código. La app lee la
variable al arrancar y decide.

**Por qué se usa aquí.** El endurecimiento de seguridad (redirigir todo a HTTPS, cookies solo por
HTTPS) tiene sentido en producción, pero **rompe los tests**: el cliente de test hace peticiones
HTTP y `SECURE_SSL_REDIRECT` las respondería con una redirección **301** en vez de procesarlas.
Hacía falta que el mismo código se comportara distinto según el entorno.

**Cómo se hizo.** La app lee `DJANGO_SECURE_HARDENING` (por defecto `not DEBUG`): activo en
producción, inactivo en desarrollo. El **CI** lo fija a `0` para correr los tests sin ese
endurecimiento. Así la app queda **agnóstica al runner** (no "sabe" si corre bajo pytest): solo
lee una variable, y cada entorno decide su comportamiento con su propia configuración, sin tocar
código.

**Ventaja sobre la alternativa.** Detectar el runner desde el código (p. ej. "¿estoy bajo
pytest?") **acopla** la app a su herramienta de test (un *code smell*). Gatear por variable de
entorno mantiene la separación: el código expone una palanca, el entorno la acciona. Es el
principio de **config por entorno** (Twelve-Factor App): el mismo binario/imagen se comporta
distinto según su configuración, no según ramas de código específicas del entorno.

## Qué se hizo
Se integró **django-allauth en modo headless** con sus **dos clientes**:
- **Navegador (web):** inicia sesión con email y contraseña; mantiene la sesión por **cookie** y
  exige **CSRF** en el login.
- **App (escritorio/Tauri):** inicia sesión y recibe un **token de sesión** que envía en la
  cabecera **`X-Session-Token`**.

Incluye:
- **Modelo `User` custom** mínimo (email como identificador, único, normalizado a minúsculas) —
  placeholder que la feature de "modelos completos" extenderá.
- **Cuenta local por email** (sin signup ni verificación de email, es de prueba); consulta de la
  sesión actual y rechazo de credenciales inválidas.
- **CORS** con credenciales para los orígenes de Tauri (multiplataforma, configurables por entorno).
- **Endurecimiento en producción**: cookies `Secure`/`HttpOnly`, redirección a HTTPS y
  reconocimiento del HTTPS reenviado por el proxy. Se activa según `DJANGO_SECURE_HARDENING`
  (por defecto `not DEBUG`); en tests/CI se desactiva (`DJANGO_SECURE_HARDENING=0`) para que el
  cliente de test HTTP no reciba redirecciones 301.
- **IP real tras proxy**: middleware que toma la última entrada de `X-Forwarded-For`.
- Comando **`seed_test_user`** para crear el usuario de prueba por CLI.
- Rate limiting **desactivado** en esta prueba (se reactivará en la auth definitiva).

Calidad: 27 tests en verde, cobertura 99 %, `ruff`/`black`/`mypy` limpios. Validación
independiente **CUMPLIDA** (ver `spec.md` → Historial).

## Cómo probarlo (usuario)
Requisitos: **Podman**. Terminal en la raíz del repo, en `main` actualizado (la feature ya está
fusionada).

**Prueba automática (rápida):** usa el contenedor de test de la red de Podman.
```powershell
podman exec conf-test pytest apps/accounts/tests/ -v --no-cov
```

**Prueba en vivo por HTTP.** Resetea la BD de dev (por el cambio de `AUTH_USER_MODEL`) y levanta
el stack, un comando cada vez:
```powershell
podman compose -f docker/docker-compose.yml down -v
```
```powershell
podman compose -f docker/docker-compose.yml build backend
```
```powershell
podman compose -f docker/docker-compose.yml up -d db redis backend
```
```powershell
podman compose -f docker/docker-compose.yml exec backend python manage.py migrate
```
```powershell
podman compose -f docker/docker-compose.yml exec backend python manage.py seed_test_user
```

Cliente **app (token)**. Inicia sesión:
```powershell
podman compose -f docker/docker-compose.yml exec backend http POST localhost:8000/_allauth/app/v1/auth/login email=test@example.com password=test-password-123
```
La respuesta trae `meta.session_token`; en el comando siguiente, `<TOKEN>` es ese valor. Consulta
la sesión autenticada con el token:
```powershell
podman compose -f docker/docker-compose.yml exec backend http GET localhost:8000/_allauth/app/v1/auth/session X-Session-Token:<TOKEN>
```

Cliente **navegador (cookie + CSRF)**. Pide la sesión sin haber iniciado sesión:
```powershell
podman compose -f docker/docker-compose.yml exec backend http --session=web GET localhost:8000/_allauth/browser/v1/auth/session
```
Responde 401 y entrega la cookie `csrftoken` (es normal, aún no hay login). En el comando
siguiente, `<CSRFTOKEN>` es el valor de esa cookie, que aparece en la cabecera `Set-Cookie` de la
respuesta. Inicia sesión enviando el `csrftoken` como cabecera:
```powershell
podman compose -f docker/docker-compose.yml exec backend http --session=web POST localhost:8000/_allauth/browser/v1/auth/login email=test@example.com password=test-password-123 X-CSRFToken:<CSRFTOKEN>
```
Vuelve a pedir la sesión:
```powershell
podman compose -f docker/docker-compose.yml exec backend http --session=web GET localhost:8000/_allauth/browser/v1/auth/session
```
Deberías ver 200, autenticado por la cookie de sesión.

Credenciales del usuario de prueba: `test@example.com` / `test-password-123`.
