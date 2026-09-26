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
Requisitos: **Podman**. Terminal en la raíz del repo, rama `feat/auth-headless`.

**Prueba automática (rápida):** usa el contenedor de test de la red de Podman.
```powershell
podman exec conf-test pytest apps/accounts/tests/ -v --no-cov
```

**Prueba en vivo por HTTP.** Resetea la BD de dev (por el cambio de `AUTH_USER_MODEL`) y levanta
el stack:
```powershell
podman compose -f docker/docker-compose.yml down -v
podman compose -f docker/docker-compose.yml build backend
podman compose -f docker/docker-compose.yml up -d db redis backend
podman compose -f docker/docker-compose.yml exec backend python manage.py migrate
podman compose -f docker/docker-compose.yml exec backend python manage.py seed_test_user
```

Cliente **app (token)**:
```powershell
# Login → devuelve meta.session_token
podman compose -f docker/docker-compose.yml exec backend http POST localhost:8000/_allauth/app/v1/auth/login email=test@example.com password=test-password-123
# Sesión autenticada con el token
podman compose -f docker/docker-compose.yml exec backend http GET localhost:8000/_allauth/app/v1/auth/session X-Session-Token:<TOKEN>
```

Cliente **navegador (cookie + CSRF)**:
```powershell
# 1) 401 + entrega la cookie csrftoken (es normal, aún no hay login)
podman compose -f docker/docker-compose.yml exec backend http --session=web GET localhost:8000/_allauth/browser/v1/auth/session
# 2) Login enviando el csrftoken como cabecera
podman compose -f docker/docker-compose.yml exec backend http --session=web POST localhost:8000/_allauth/browser/v1/auth/login email=test@example.com password=test-password-123 X-CSRFToken:<CSRFTOKEN>
# 3) 200 autenticado (por cookie de sesión)
podman compose -f docker/docker-compose.yml exec backend http --session=web GET localhost:8000/_allauth/browser/v1/auth/session
```

Credenciales del usuario de prueba: `test@example.com` / `test-password-123`.
