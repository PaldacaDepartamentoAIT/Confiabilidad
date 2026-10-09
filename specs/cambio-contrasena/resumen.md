# Resumen — cambio-contrasena
Estado: implementada, pendiente de validación · Última actualización: 2026-10-09

## Qué se hizo
Quien olvidó su contraseña puede fijar una nueva demostrando acceso al correo de su cuenta con un
código. Todo se recorre desde consola con `manage.py password_reset`, sin frontend ni API
(RF-013). La API será otra feature y usará el mismo servicio (`apps/accounts/password_reset.py`).

- **Solicitud de cambio de contraseña** (`PasswordResetRequest`, migración `0006`): una por cuenta,
  garantizada por la base de datos, y se borra con la cuenta (RF-001, RF-010). No guarda `used_at`
  (S-02): se borra al completarse o al purgarse.
- **Pedir el cambio** (`start --email`): con una cuenta activa crea la solicitud o la reemplaza
  (identificador público y código nuevos, intentos a 0, sin validar, vida contada de nuevo). Sin
  cuenta o con la cuenta inactiva, el resultado es el mismo, "sin cuenta elegible", y no se toca
  nada (RF-002…RF-004).
- **Mismas reglas de código que el registro**: 6 dígitos, 15 min de vigencia, 5 intentos, 15 min de
  gracia, 1 h de vida y rotación del secreto, con los mismos ajustes `REGISTRATION_*` (RF-005…RF-007,
  RF-012). El código del registro y el de la solicitud ya no comparten huella: cada una lleva su
  tipo de proceso (D-01).
- **La solicitud deja de servir** si la cuenta se desactiva (vuelve a servir si se reactiva antes de
  caducar) o si, después de pedirla, cambian el correo o la contraseña de la cuenta (RF-008,
  RF-014, RF-015).
- **Completar** (`complete`): fija la contraseña con la política del proyecto (evaluada con el correo
  y el nombre de la cuenta), marca el correo como verificado, borra los inicios de sesión fallidos
  que allauth llevaba para ese correo y borra la solicitud, todo o nada (RF-009). La contraseña
  actual se acepta si cumple la política.
- **Sesiones abiertas**: tras completar, las sesiones del navegador y los tokens de la app dejan de
  autenticar (401), porque Django ata cada sesión al hash de la contraseña. No se borran: siguen
  guardadas en Redis hasta caducar, inservibles. Borrarlas es del flujo (S-03).
- **Limpieza**: `password_reset purge` borra las solicitudes caducadas; `registration purge` sigue
  borrando solo registros pendientes (RF-011).
- **Reutilización**: el registro y el cambio de contraseña comparten la base del modelo
  (`CodeProcess`), las operaciones del código (`processes.py`) y las utilidades de consola
  (`management/console.py`). El comportamiento del registro no cambió; su suite sigue en verde.

### Límites conocidos
- **Sin límite de frecuencia** (S-05): pedir de nuevo o reenviar ponen los intentos a 0. En consola
  no hay riesgo; **la API no debe publicarse sin ese límite**, porque permitiría tomar cuentas
  ajenas (anotado en `HUMAN_TODO.md`).
- **"Sin cuenta elegible" es distinguible en el servicio** (RF-004): a propósito, porque en consola
  no se puede ocultar (el comando muestra el código). **La API debe neutralizarlo** con el mismo
  mensaje y un tiempo de respuesta comparable (anotado en `HUMAN_TODO.md`).
- La concurrencia (dos peticiones a la vez para la misma cuenta) está protegida con bloqueos de
  fila en un orden fijo (cuenta → solicitud), pero ningún test la ejerce con transacciones reales.
- El borrado del contador de inicios fallidos usa funciones internas de allauth; si una
  actualización las cambia, el test `test_completing_clears_the_failed_login_counter` falla.
- Si Django vuelve a calcular el hash de una contraseña al iniciar sesión (por ejemplo, tras
  actualizar Django), una solicitud en curso de esa cuenta deja de servir y hay que pedir otra.
- Si una dirección de correo verificada en allauth pertenece a otra cuenta (posible si se cambió un
  correo desde el panel sin actualizar allauth), `complete` falla sin dejar nada a medias. El
  problema ya existía en el registro.
- En la sesión remota, la imagen de Docker se construyó con una copia del `Dockerfile` que añade el
  certificado del proxy de la sesión solo durante `pip install`. Con ella, `0006` se aplicó, los
  servicios arrancaron y la suite pasó dentro del contenedor. Falta construirla con el `Dockerfile`
  real fuera de la sesión (anotado en `HUMAN_TODO.md`).
- Si se ejecuta la suite con el `worker` de Compose en marcha, `apps/core/tests/test_task_worker.py`
  falla: el worker comparte el broker y se lleva la tarea del test. Es previo a esta feature.

## Cómo probarlo
Requisitos: Docker y la rama `feat/cambio-contrasena`. En el VPS sigue *Actualizar* y
*Migraciones* de la sección *Entorno remoto* del README.

1. Levanta la base de datos y Redis, y aplica las migraciones. Deberías ver
   `accounts.0006_passwordresetrequest... OK`:
   `docker compose -f docker/docker-compose.yml up -d db redis`
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate`
   En los pasos siguientes, `R` abrevia
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration`
   y `P` abrevia
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset`.
2. Crea una cuenta con el registro (si ya tienes una, salta este paso):
   `R start --email Eva@Example.com --name "Eva Pérez" --birthdate 1991-03-04 --country es`
   `R verify <public_id> <code>` y `R complete <public_id> --password 'Kq7#mZ2!vR9p'`.
3. Pide el cambio con un correo sin cuenta: `P start --email nadie@example.com` →
   `No active account with this email.`
4. Pide el cambio para la cuenta (mayúsculas y espacios dan igual). Verás `public_id: …` y
   `code: …`; anótalos:
   `P start --email " EVA@example.com "`
5. Prueba un código erróneo: `P verify <public_id> 000000` → `Wrong code.`
6. Pide un código nuevo: `P resend <public_id>` → el mismo `public_id` y otro `code`.
7. Verifica el código nuevo: `P verify <public_id> <code>` → `Code verified.`
8. Completa. Primero con una contraseña débil, para ver cada regla incumplida:
   `P complete <public_id> --password 12345678`
   Después sin `--password`: te la pedirá sin mostrarla (usa 12 caracteres o más):
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset complete <public_id>`
   Verás `account: eva@example.com`.
9. Comprueba que la nueva contraseña inicia sesión (debe imprimir `200`):
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from django.test import Client; print(Client().post('/_allauth/app/v1/auth/login', data={'email': 'eva@example.com', 'password': 'TU-CONTRASEÑA'}, content_type='application/json', HTTP_HOST='localhost').status_code)"`
10. Comprueba que una solicitud deja de servir si cambia la contraseña por otra vía: repite el paso
    4, cambia la contraseña con `docker compose -f docker/docker-compose.yml run --rm backend python manage.py changepassword eva@example.com`
    y verifica el código: `P verify <public_id> <code>` →
    `The account's email or password changed after the request; start again.`
11. Purga las caducadas: `P purge` → `deleted: N`.
12. Ejecuta la suite completa (cobertura mínima 80 % sobre todo el proyecto):
    `docker compose -f docker/docker-compose.yml run --rm backend pytest -q`

## Marco teórico
### Enumeración de cuentas y "sin cuenta elegible"
Si un sistema responde distinto según exista o no una cuenta con un correo, cualquiera puede
averiguar qué correos están registrados probando una lista. Por eso el flujo dice siempre "Si
existe una cuenta, recibirás un código". El servicio de esta feature sí distingue
(`NoEligibleAccount`) porque solo lo usa la consola, que ya tiene acceso a todo y además muestra el
código, así que no hay nada que ocultar. La protección se traslada a la API: debe responder igual
**en el mensaje y en el tiempo**. El tiempo importa: con cuenta, el servidor escribe en la base de
datos y calcula una huella; sin cuenta, no. Si una respuesta tarda sistemáticamente más, delata la
cuenta igual que un mensaje distinto.

### Separación de dominio en una huella
Una huella HMAC demuestra que alguien conocía un dato (el código) en un contexto concreto (el
proceso). Si dos procesos firman con el mismo secreto y el mismo formato, una huella de uno podría,
en teoría, valer en el otro. Añadir el tipo de proceso al mensaje (`password_reset:…` frente a
`registration:…`) separa los "dominios": la garantía queda en la propia huella y no depende de que
las tablas estén separadas o de que los identificadores sean imposibles de elegir.

### Huella de la cuenta
Para saber si el correo o la contraseña de la cuenta cambiaron después de pedir el cambio, la
solicitud guarda una huella de ambos (correo + hash de la contraseña) en lugar de una copia. Si al
verificar o completar la huella ya no coincide, algo cambió y la solicitud deja de servir. Así no se
duplica el correo ni el hash de la contraseña en otra tabla; es la misma idea que usan los enlaces
de restablecimiento de Django.

### Por qué las sesiones dejan de valer sin borrarlas
Django guarda en cada sesión una huella derivada del hash de la contraseña. En cada petición la
compara con la de la cuenta: si la contraseña cambió, no coincide y la sesión se trata como cerrada
(401). La sesión sigue almacenada en Redis hasta caducar, pero ya no sirve.
