# Resumen — cambio-contrasena
Estado: cambio del 2026-10-14 implementado, pendiente de validar · Última actualización: 2026-10-15

## Qué se hizo
Quien olvidó su contraseña puede fijar una nueva demostrando acceso al correo de su cuenta con un
código. Todo se recorre desde consola con `manage.py password_reset`, sin frontend ni API
(RF-013). La API será otra feature y usará el mismo servicio (`apps/accounts/password_reset.py`).

- **Solicitud de cambio de contraseña** (`PasswordResetRequest`, migración `0006`): una por cuenta,
  garantizada por la base de datos, y se borra con la cuenta (RF-001, RF-010). No guarda `used_at`
  (S-02): se borra al completarse o al purgarse.
- **Pedir el cambio sin revelar si el correo tiene cuenta** (cambio del 2026-10-14, RF-016,
  RF-017). La respuesta de `start --email` solo valida el formato del correo, deja una **plaza**
  (`PhantomProcess` de propósito `password_reset`, la misma de `procesos-pendientes`) y devuelve su
  `public_id`, tenga o no cuenta el correo. Fuera de la respuesta, la tarea
  `resolve_password_reset` decide:
  - con una cuenta activa, crea la solicitud con ese `public_id` o reemplaza la que tuviera
    (código nuevo, intentos a 0, sin validar, vida contada de nuevo) y encola el correo con el
    código en el idioma de la petición (`--language`);
  - sin cuenta o con la cuenta inactiva, la plaza queda como identificador sin solicitud detrás,
    sin correo (RF-002…RF-004).

  Verificar, reenviar, completar y dejar caducar ese identificador da los mismos resultados, con
  las mismas consultas, que una solicitud real cuyo código nunca se acierta, también con una cuenta
  inactiva. Desde las correcciones del 2026-10-15, también cuando la resolución se retrasa o cuando
  alguien opera con el identificador mientras se resuelve:
  - al resolverse, la plaza sin solicitud queda como una solicitud recién emitida (intentos a 0, y
    código y vida contados desde la resolución);
  - manda la petición más reciente: si una plaza antigua se resuelve después de otra más nueva del
    mismo correo, la antigua se borra sin hacer nada;
  - todas las operaciones bloquean primero la plaza, en el mismo orden que la resolución (plaza →
    cuenta → solicitud).

  Reintentos, barrido y ventana (`REGISTRATION_START_RETRY_MINUTES`) son los del registro: la
  ventana se comprueba en cada ejecución.
- **Mismas reglas de código que el registro**: 6 dígitos, 15 min de vigencia, 5 intentos, 15 min de
  gracia, 1 h de vida y rotación del secreto, con los mismos ajustes `REGISTRATION_*` (RF-005…RF-007,
  RF-012). El código del registro y el de la solicitud ya no comparten huella: cada una lleva su
  tipo de proceso (D-01).
- **«Caducada» en vez de rechazos propios** (D-14): si la cuenta se desactiva o si, después de
  pedirla, cambian su correo o su contraseña, `verify`, `resend` y `complete` responden lo mismo que
  con una solicitud caducada, sin modificarla. Si la cuenta se reactiva antes de que caduque, vuelve
  a servir (RF-008, RF-014, RF-015). Los mensajes del comando ya no mencionan la cuenta.
- **Tumba al borrar la cuenta** (D-15, migración `0009`): antes de borrar una cuenta con solicitud,
  queda en su lugar una plaza con el mismo `public_id` y las mismas fechas que responde «caducada» a
  todo; no guarda el correo ni otros datos de la cuenta. La purga la borra al caducar (RF-010).
- **Reenvío en dos tiempos** (D-13 de `procesos-pendientes`): la respuesta anula el código vigente y
  pone los intentos a 0; la tarea `reissue_code` emite el nuevo y lo envía en el idioma de la
  petición, que la solicitud guarda desde la migración `0010` (D-17). Una plaza también recibe código
  nuevo, que nunca se envía.
- **Completar** (`complete`): fija la contraseña con la política del proyecto (evaluada con el correo
  y el nombre de la cuenta), marca el correo como verificado, borra los inicios de sesión fallidos
  que allauth llevaba para ese correo, encola el aviso «Tu contraseña se ha restablecido» en el
  idioma de la cuenta y borra la solicitud, todo o nada (RF-009, D-16). La contraseña actual se
  acepta si cumple la política.
- **Sesiones abiertas**: tras completar, las sesiones del navegador y los tokens de la app dejan de
  autenticar (401), porque Django ata cada sesión al hash de la contraseña. No se borran: siguen
  guardadas en Redis hasta caducar, inservibles. Borrarlas es del flujo (S-03).
- **Limpieza**: `password_reset purge` borra las solicitudes y las plazas de cambio de contraseña
  caducadas, tumbas incluidas, y cuenta todas; `registration purge` solo borra lo del registro
  (RF-011).
- **Reutilización**: el registro y el cambio de contraseña comparten la base del modelo
  (`CodeProcess`), las operaciones del código (`processes.py`) y las utilidades de consola
  (`management/console.py`). El comportamiento del registro no cambió; su suite sigue en verde.

### Límites conocidos
Riesgos residuales aceptados al cerrar, tras tres validaciones independientes (todas de origen
*Test*, ninguna de código): las correcciones de la última ronda (T-021…T-023) solo se comprobaron
matando los mutantes que la validación encontró, sin una cuarta validación independiente; y quedan
sin aserción directa la búsqueda de la dirección de correo sin distinguir mayúsculas, todos los
campos de la solicitud de una cuenta inactiva (RF-004) y el instante exacto de caducidad. El resto
se detalla abajo.

- **Sin límite de frecuencia** (S-05): pedir de nuevo o reenviar ponen los intentos a 0. En consola
  no hay riesgo; **la API no debe publicarse sin ese límite**, porque permitiría tomar cuentas
  ajenas (anotado en `HUMAN_TODO.md`).
- **El servicio ya no distingue «sin cuenta elegible»**: la respuesta es la misma y hace el mismo
  trabajo. A la API le queda devolver un mensaje neutro (anotado en `HUMAN_TODO.md`).
- **Tiempo de respuesta igual por construcción, no medido**: los tests fijan las mismas consultas con
  plaza y con solicitud real, pero ninguno mide tiempos reales.
- **Equivalencia probada en las secuencias conocidas, no en todas**: bloqueo, caducidad, reenvío,
  repetición, resolución retrasada, peticiones desordenadas, operación simultánea y cuenta inactiva.
  Una secuencia que nadie ha pensado podría distinguirlas todavía.
- **«Caducada» confunde al titular legítimo** (S-13): quien cambió su contraseña por otra vía, o cuya
  cuenta se desactivó, ve «caducada» y no el motivo real. Es el precio de no revelar la cuenta.
- Si se pierde el encolado de un reenvío, la solicitud se queda sin código válido hasta que se pida
  otro reenvío: `reissue_code` no tiene barrido. Sin el worker en marcha, no llega ningún código.
- La concurrencia está protegida con bloqueos de fila en un orden fijo (plaza → cuenta →
  solicitud). Un test con transacciones reales y dos hilos ejerce una operación simultánea a la
  resolución; dos peticiones a la vez para la misma cuenta no se ejercen así.
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
Requisitos: Docker y `main` actualizado. En el VPS sigue *Actualizar* y *Migraciones* de la sección
*Entorno remoto* del README. Todos los comandos se ejecutan desde la raíz del repositorio. Sin
proveedor de correo configurado, los correos salen por la consola del worker: ahí se leen los
códigos.

1. Levanta la base de datos y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   Aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver, entre otras, `accounts.0009_phantom_answers_expired... OK` y
   `accounts.0010_passwordresetrequest_language... OK`. Levanta el worker y el
   planificador de Celery:
   ```bash
   docker compose -f docker/docker-compose.yml up -d worker beat
   ```

2. Crea una cuenta con el registro (si ya tienes una, salta al paso 3):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email Eva@Example.com --name "Eva Pérez" --birthdate 1991-03-04 --country es
   ```
   Deberías ver `public_id: …`; en los comandos siguientes, `<PUBLIC_ID_REGISTRO>` es ese valor. Lee
   el código en la salida del worker:
   ```bash
   docker compose -f docker/docker-compose.yml logs worker --tail 60
   ```
   Deberías ver el correo «Confirma tu correo para crear tu cuenta» con un código de 6 dígitos; en
   el comando siguiente, `<CODE_REGISTRO>` es ese código:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID_REGISTRO> <CODE_REGISTRO>
   ```
   Deberías ver `Code verified.`. Completa el registro con el mismo `<PUBLIC_ID_REGISTRO>`:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID_REGISTRO> --password 'Kq7#mZ2!vR9p'
   ```
   Deberías ver `account: eva@example.com`.

3. Pide el cambio con un correo sin cuenta:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset start --email nadie@example.com
   ```
   Deberías ver solo `public_id: …`, igual que con una cuenta. En el comando siguiente,
   `<OTHER_ID>` es ese valor:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset verify <OTHER_ID> 000000
   ```
   Deberías ver `Wrong code.`, como en una solicitud real; nunca llega correo a ese identificador.

4. Pide el cambio para la cuenta (las mayúsculas y los espacios dan igual):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset start --email " EVA@example.com " --language es
   ```
   Deberías ver `public_id: …`. En los pasos siguientes, `<PUBLIC_ID>` es ese valor. Repite el
   comando de `logs` del paso 2: llega «Tu código para restablecer la contraseña».

5. Prueba un código erróneo con el `<PUBLIC_ID>` del paso 4:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset verify <PUBLIC_ID> 000000
   ```
   Deberías ver `Wrong code.`.

6. Pide un código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset resend <PUBLIC_ID>
   ```
   Deberías ver solo el mismo `public_id`. Repite el comando de `logs` del paso 2: el correo más
   reciente trae otro código. En el paso siguiente, `<CODE>` es ese código nuevo.

7. Verifica el código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset verify <PUBLIC_ID> <CODE>
   ```
   Deberías ver `Code verified.`.

8. Completa primero con una contraseña débil, para ver cada regla incumplida:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset complete <PUBLIC_ID> --password 12345678
   ```
   Deberías ver una línea por regla incumplida (longitud, contraseña común y solo números). Después
   complétalo sin `--password`; te pedirá la contraseña sin mostrarla (usa 12 caracteres o más):
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset complete <PUBLIC_ID>
   ```
   Deberías ver `account: eva@example.com`. En los `logs` del worker aparece el aviso «Tu contraseña
   se ha restablecido».

9. Comprueba que la nueva contraseña inicia sesión. `<NUEVA_CONTRASEÑA>` es la que escribiste en el
   paso 8:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from django.test import Client; print(Client().post('/_allauth/app/v1/auth/login', data={'email': 'eva@example.com', 'password': '<NUEVA_CONTRASEÑA>'}, content_type='application/json', HTTP_HOST='localhost').status_code)"
   ```
   Deberías ver `200`.

10. Comprueba que una solicitud responde «caducada» si la contraseña cambia por otra vía. Pide una
    solicitud nueva:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset start --email eva@example.com
    ```
    Anota el `public_id` y lee su código en los `logs` del worker. Cambia la contraseña desde la
    consola de Django (te la pedirá dos veces):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py changepassword eva@example.com
    ```
    Verifica el código de la solicitud; `<PUBLIC_ID>` y `<CODE>` son los que anotaste:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset verify <PUBLIC_ID> <CODE>
    ```
    Deberías ver `The password reset request has expired; start again.`.

11. Purga lo caducado:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py password_reset purge
    ```
    Deberías ver `deleted: N`, que suma solicitudes y plazas.

12. Para el `worker` de Compose (comparte el broker con los tests y hace fallar
    `apps/core/tests/test_task_worker.py`):
    ```bash
    docker compose -f docker/docker-compose.yml stop worker
    ```
    Ejecuta la suite completa (cobertura mínima del 80 % sobre todo el proyecto):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend pytest -q
    ```
    Deberías ver todos los tests en verde y `Required test coverage of 80% reached`.

## Marco teórico
### Enumeración de cuentas y "sin cuenta elegible"
Si un sistema responde distinto según exista o no una cuenta con un correo, cualquiera puede
averiguar qué correos están registrados probando una lista. Por eso el flujo dice siempre "Si
existe una cuenta, recibirás un código". Debe responder igual **en el mensaje y en el tiempo**: si
con cuenta el servidor escribe la solicitud y calcula la huella y sin cuenta no, la respuesta que
tarda más delata la cuenta. Desde el cambio del 2026-10-14, la respuesta solo guarda una plaza en
los dos casos y el trabajo que depende de la cuenta se hace después, en el worker.

### Plaza, identificador sin solicitud y tumba
La plaza es una fila con un `public_id` que se guarda para toda petición válida. Si el correo tiene
una cuenta activa, se convierte en la solicitud real; si no, queda como identificador «vacío» que no
acepta ningún código pero cuenta intentos, se bloquea y caduca como uno real. La tumba es una plaza
que ocupa el lugar de la solicitud de una cuenta borrada y responde «caducada» a todo: así,
desaparecer la cuenta no se nota en las respuestas.

### Por qué «caducada» y no el motivo real
Una plaza nunca puede responder «la cuenta está inactiva» o «la cuenta cambió», porque no hay
cuenta detrás. Si una solicitud real sí lo respondiera, esa respuesta delataría que el correo tenía
cuenta. Por eso todos esos casos responden lo mismo que una solicitud caducada, que es una
respuesta que cualquier identificador puede dar.

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

Desde `huellas-hmac-unificadas`, la huella del código y la de la cuenta se calculan y se comprueban
en `backend/apps/core/fingerprints.py` (`code_fingerprint` / `code_matches` y `account_stamp` /
`account_stamp_matches`). El correo de la huella de la cuenta se normaliza ahora igual que en
consentimientos (sin espacios a los lados, además de en minúsculas); como los correos de las
cuentas ya se guardan así, ninguna huella guardada cambia.

### Por qué las sesiones dejan de valer sin borrarlas
Django guarda en cada sesión una huella derivada del hash de la contraseña. En cada petición la
compara con la de la cuenta: si la contraseña cambió, no coincide y la sesión se trata como cerrada
(401). La sesión sigue almacenada en Redis hasta caducar, pero ya no sirve.
