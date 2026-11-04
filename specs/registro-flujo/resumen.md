# Resumen — registro-flujo

## Qué se hizo
El registro de una cuenta se puede hacer de principio a fin en la web (y en el escritorio, que carga
la misma web): formulario, verificación del correo con un código de 6 dígitos y elección de la
contraseña. Cada entrega tiene su propio resumen en `entregas/`.

**Backend** (`backend/apps/accounts/`):
- Servicio del flujo (`registration.py`): verificar el código (que queda validado, no usado),
  consultar el estado (tiempo restante, espera y reenvíos restantes, bloqueo), reenviar con espera de
  60 s y como mucho 5 veces, y crear la cuenta en una sola transacción con el código y la
  contraseña (usuario, correo verificado, aceptación de términos y, si se marcó, marketing; el
  código se marca como usado y el registro pendiente se borra).
- Un identificador sin registro detrás (una «plaza») responde igual que uno real hasta que se borra,
  y los dos pasan a `404` a la vez. Un identificador desconocido responde `404`.
- API en `/api/app/v1/registration/…` y `/api/browser/v1/registration/…` (esta con CSRF): `options`
  (países, términos y marketing vigentes; da la cookie CSRF), `status`, `verify`, `resend` y
  `complete`, con un límite de 60 peticiones por hora e IP para todo el flujo salvo `status`.
- Limpieza (`purge_stale`): los registros sin verificar se borran 24 h después de caducar su último
  código, con una tarea de Celery cada hora y el subcomando `registration purge-stale`.

**Frontend** (`frontend/src/`):
- Cliente de la API (`api/`): rutas `browser` con CSRF en la web y `app` en Tauri.
- Pantallas en `registration/`: formulario (`/register`), verificación con reenvío y paso de
  contraseña (`/register/continue#<identificador>`) y cuenta creada (`/register/done`).
- Componentes y validación ampliados: casilla, selector, fecha, varios errores por campo,
  desplazamiento al primer error, dígitos como el servidor y cuenta atrás.
- Identidad visual Niebla marina (Manrope y JetBrains Mono, temas claro y oscuro según el sistema)
  y textos en `es`, `pt-BR` y `en`. Los términos se muestran como Markdown sin HTML
  (`react-markdown`).

### Entregas
| Entrega | PR |
|---|---|
| E-01 Código validado | [#34](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/34) |
| E-02 Verificar por la API | [#35](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/35) |
| E-03 Reenvío | [#36](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/36) |
| E-04 Estado | [#37](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/37) |
| E-05 Completar | [#38](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/38) |
| E-06 Marketing | [#39](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/39) |
| E-07 Limpieza | [#41](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/41) |
| E-08 Identidad visual | [#42](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/42) |
| E-09 Cliente de la API | [#43](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/43) |
| E-16 Llamadas del registro | [#44](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/44) |
| E-10 Campos y validación | [#45](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/45) |
| E-11 Dígitos y cuenta atrás | [#46](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/46) |
| E-12 Textos | [#47](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/47) |
| E-18 Formulario | [#48](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/48) |
| E-19 Envío del formulario | [#49](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/49) |
| E-13 Verificación | [#50](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/50) |
| E-20 Código, bloqueo y reenvío | [#51](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/51) |
| E-14 Paso de contraseña | [#52](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/52) |
| E-21 Cuenta creada | [#53](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/53) |
| E-15 Registro completo en la web | pendiente |

### Límites conocidos
- La pantalla de cuenta creada no ofrece salida: el inicio de sesión no es de esta feature (S-07).
- Riesgos aceptados por el usuario: las reglas de la contraseña y los valores de los textos de error
  (150 caracteres, 18 años y 5 días) están copiados a mano del servidor; 80 dígitos de escrituras
  de Unicode 16 cuentan como dígito en el navegador y no en el servidor; la contraseña no tiene
  longitud máxima; el reenvío rechazado de un código validado responde como el de una plaza (D-05).
- Los tests de accesibilidad corren en jsdom, que no puede medir el contraste: el contraste de cada
  texto sobre su fondo solo se comprueba a mano o en un navegador real.
- El selector de fecha nativo muestra el formato del idioma del navegador, no el de la página.

## Cómo probarlo
### En la web
1. Levanta los servicios (los valores de desarrollo bastan; `backend/.env` es opcional):
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis backend worker frontend
   ```
2. Aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml exec backend python manage.py migrate
   ```
3. Crea los términos vigentes: sigue el paso 3 de `specs/consentimientos/resumen.md` (documentos
   *Terms of use* `1` y *Marketing* `m1` en `es`, `pt-BR` y `en`, publicados ayer). Sin términos
   vigentes, el formulario dice que ahora no es posible registrarse.
4. Abre http://localhost:5173/register. Pulsa «Continuar» sin rellenar nada: deberías ver el error
   de cada campo y el foco en el primero. Rellena el formulario con un correo tuyo de prueba y pulsa
   «Continuar»: deberías llegar a «Escribe el código de verificación», con el tiempo restante
   contando y el botón de reenvío con su espera.
5. Lee el correo en la consola del worker (el proveedor local escribe el correo completo allí):
   ```bash
   docker compose -f docker/docker-compose.yml logs worker
   ```
   Deberías ver «Tu código para confirmar tu correo es:» seguido de 6 dígitos, y un enlace
   `http://localhost:5173/register/continue#…` que abre la misma pantalla.
6. Escribe `000000` y pulsa «Verificar»: deberías ver «El código no es correcto…» bajo el campo.
   Escribe el código del correo: debería aparecer «Elige tu contraseña».
7. Prueba `password1234`: deberías ver «Esta contraseña es demasiado común.» bajo el campo. Escribe
   una contraseña larga y poco común y pulsa «Crear cuenta»: deberías llegar a «Cuenta creada».
8. Vuelve a abrir el enlace del correo: deberías ver «Enlace no válido».

### Con curl (sin frontend)
Pide las opciones del formulario:
```bash
curl -s "http://localhost:8000/api/app/v1/registration/options?language=es"
```
Deberías ver la lista de países y los términos vigentes. Empieza un registro:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration -H "Content-Type: application/json" -d '{"name":"Luis Gómez","birthdate":"1988-05-10","email":"luis@planta.com","country":"ES","terms":{"accepted":true,"version":"1","locale":"es"},"language":"es"}'
```
Deberías ver un `public_id` y el mensaje neutro. En los pasos siguientes, `<PUBLIC_ID>` es ese
valor y `<CODIGO>` los 6 dígitos del correo que muestra el worker (paso 5 de la web). Consulta el
estado:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/status -H "Content-Type: application/json" -d '{"public_id":"<PUBLIC_ID>"}'
```
Deberías ver `code_expires_in`, `resend_in`, `resends_left`, `locked` y `expired`. Verifica el código:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/verify -H "Content-Type: application/json" -d '{"public_id":"<PUBLIC_ID>","code":"<CODIGO>"}'
```
Deberías ver `{"result":"verified"}`. Crea la cuenta:
```bash
curl -s -X POST http://localhost:8000/api/app/v1/registration/complete -H "Content-Type: application/json" -d '{"public_id":"<PUBLIC_ID>","code":"<CODIGO>","password":"turbina-compresor-7-marea"}'
```
Deberías ver `{"result":"created"}`. Repite la consulta de estado: deberías ver `not_found`, porque
el registro pendiente ya no existe.

### Limpieza de registros caducados
La tarea `accounts-purge-stale-registrations` de Celery beat la ejecuta cada hora. Para lanzarla a
mano:
```bash
docker compose -f docker/docker-compose.yml exec backend python manage.py registration purge-stale
```
Deberías ver `deleted: N`, con N los registros y plazas cuyo último código caducó hace más de 24 h.

### Tests
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q
```
```bash
pnpm --filter frontend test
```
Deberías ver todos los tests en verde.

## Marco teórico
### Código validado frente a código usado
Validar el código (pantalla de verificación) solo demuestra que la persona lo tiene; el código se
da por usado al crear la cuenta. Así, si cierra la pestaña tras validarlo, puede volver con el enlace
y presentarlo otra vez, mientras no caduque ni se agoten los intentos.

### El código solo en memoria
El código aceptado vive en la memoria de la página, no en la URL ni en el almacenamiento del
navegador: no queda en el historial ni en disco. Recargar obliga a escribirlo otra vez, y el
servidor lo vuelve a comprobar en cada intento de crear la cuenta.

### El identificador en el fragmento (`#`)
El navegador no envía al servidor lo que va después de `#`: el identificador no aparece en los
registros de acceso ni en la cabecera `Referer`. La pantalla lo lee y lo manda en el cuerpo.

### CSRF, `Origin` y el proxy de desarrollo
Django rechaza un `POST` de las rutas web si la cabecera `Origin` del navegador no coincide con el
`Host` de la petición. En desarrollo, Vite reenvía `/api` al backend; si reescribe el `Host` al del
backend, los dos ya no coinciden y todo `POST` da `403`. Por eso el proxy conserva el `Host` del
navegador (T-054).

### Un clic que se pierde por un desplazamiento
Al pulsar un control, el campo anterior pierde el foco y se valida. Si su error aparece o
desaparece, todo lo que hay debajo se mueve antes de soltar el botón, y el clic cae en otro sitio.
La validación de un campo que se deja con un clic espera a que el clic termine (T-055).

### Indistinguibilidad de la plaza
Responder distinto a un identificador inventado que a uno real permitiría saber si un correo está en
proceso de registro. La plaza hace el mismo trabajo que un registro real (mismas consultas) y los
dos pasan a «no encontrado» a la vez. Más detalle en `specs/procesos-pendientes/resumen.md`.
