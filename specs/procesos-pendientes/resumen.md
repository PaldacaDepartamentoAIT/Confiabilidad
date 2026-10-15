# Resumen — procesos-pendientes
Estado: cambio del 2026-10-14 implementado, pendiente de validar · Última actualización: 2026-10-15

## Qué se hizo
El registro pasa por un **registro pendiente**: la cuenta no existe hasta que se demuestra el
acceso al correo con un código y se fija una contraseña. Todo se puede recorrer desde consola con
`manage.py registration`, sin frontend ni API (RF-023). La API será la feature siguiente y usará el
mismo servicio (`apps/accounts/registration.py`).

- **Registro pendiente** (`PendingRegistration`, migración `0005`): correo, nombre, fecha de
  nacimiento y país, validados con las mismas reglas que la cuenta; un solo registro por correo sin
  distinguir mayúsculas y `public_id` único, garantizados por la base de datos (RF-001…RF-004).
- **Empezar el registro sin revelar si el correo tiene cuenta** (cambio del 2026-10-14, RF-024,
  RF-025). La respuesta de `start` solo valida los datos y deja una **plaza** (`PhantomProcess`,
  migración `0008`) con un `public_id` nuevo; devuelve ese identificador y nada más, tenga o no
  cuenta el correo. Fuera de la respuesta, la tarea `resolve_registration` de Celery decide:
  - sin cuenta, la plaza se convierte en registro pendiente con el mismo `public_id` y se encola el
    correo con el código;
  - con cuenta, la plaza se queda como **identificador sin registro detrás** y, si la cuenta está
    activa, se encola el aviso "ya tienes cuenta".

  Verificar, reenviar, completar y dejar caducar ese identificador da los mismos resultados, con
  las mismas consultas, que un registro real cuyo código nunca se acierta. Desde las correcciones
  del 2026-10-15, también cuando la resolución se retrasa, cuando se repite el correo con el paso del
  tiempo o cuando alguien opera con el identificador mientras se resuelve:
  - al resolverse, la plaza con cuenta queda como un registro recién emitido (intentos a 0 y código
    vigente desde la resolución) y conserva el alta de la plaza vigente que reemplaza, igual que un
    registro repetido conserva la suya;
  - manda la petición más reciente: si una plaza antigua se resuelve después de otra más nueva del
    mismo correo, la antigua se borra sin hacer nada;
  - verificar, reenviar y completar bloquean primero la plaza, en el mismo orden que la resolución.

  Si la tarea falla, se reintenta durante `REGISTRATION_START_RETRY_MINUTES` (5 min), sin otro
  tope; la ventana se comprueba en cada ejecución, así que un reintento o una tarea que la cola
  atiende tarde no resuelve fuera de ella. Un barrido cada 60 s recoge las plazas cuyo encolado se
  perdió; pasada la ventana, la plaza queda sin registro, no se envía correo y el fallo va al log.
- **Código de 6 dígitos** vigente 15 min. Solo se guarda su huella (HMAC con un secreto del
  servidor y atada al `public_id`); el código en claro solo viaja en el correo (RF-007, RF-008). El
  secreto se puede rotar sin invalidar los códigos en curso (RF-015).
- **Verificación**: 5 intentos fallidos bloquean el código hasta pedir otro (RF-009, RF-010).
- **Caducidad**: el proceso muere 15 min después de caducar su código o 1 h después del alta, lo
  que llegue antes (RF-011). La gracia sirve para completar tras validar el código.
- **Reenvío en dos tiempos** (RF-016): la respuesta anula el código vigente y pone los intentos a
  0; la tarea `reissue_code` emite el código nuevo y lo envía por correo. Mismo `public_id`. Una
  plaza también recibe un código nuevo, que nunca se envía.
- **Registro repetido** con un registro vigente: conserva los datos, emite `public_id` y código
  nuevos y anula la validación, para que nadie se apropie de un registro ajeno (RF-005, S-06).
- **Completar**: crea la cuenta con el correo verificado y borra el registro, todo o nada; si el
  correo consiguió cuenta entretanto, rechaza y borra el registro (RF-012, RF-020).
- **Política de contraseñas** de todo el proyecto: 12 caracteres o más, no parecida al correo ni
  al nombre, no común y no filtrada según Have I Been Pwned, consultado sin enviar la contraseña.
  Si el servicio no responde, se acepta y se registra un aviso (RF-022, S-09).
- **Limpieza**: `registration purge` borra los registros pendientes y las plazas de registro
  caducados, y cuenta los dos (RF-013).
- **Límites configurables** por variables de entorno (RF-019); ver `backend/.env.example`.

### Límites conocidos
Riesgos residuales aceptados al cerrar (dos validaciones independientes): la concurrencia sin
probar con transacciones reales, el `IntegrityError` de `complete`, Have I Been Pwned sin probar
contra el servicio real y `makemessages` sin ejecutar. Se detallan abajo.

- **Reenvío sin límite de frecuencia** (S-01, S-07): cada reenvío reinicia los intentos, así que
  el tope de 5 es por código, no por proceso. Sin riesgo en consola; **la API no debe publicarse
  sin ese límite** (anotado en `HUMAN_TODO.md`).
- **Contraseñas filtradas sin probar contra el servicio real**: los tests lo simulan y en el
  entorno de desarrollo remoto no hay salida a internet. En una máquina con red se consulta de
  verdad.
- `--password` deja la contraseña en el historial de la consola; sin él, `complete` la pide sin
  eco (D-09).
- La concurrencia está protegida con bloqueos de fila. Un test con transacciones reales y dos hilos
  ejerce una operación simultánea a la resolución; el resto de combinaciones (dos verificaciones o
  dos altas a la vez) no se ejerce así.
- Si otra vía crea la cuenta justo entre la comprobación y el alta en `complete`, sale un
  `IntegrityError` sin traducir y el registro pendiente se conserva, en vez de borrarse, hasta el
  siguiente intento; la base de datos impide el duplicado igualmente. Hay que traducirlo antes de
  la API (anotado en `HUMAN_TODO.md`).
- Un secreto de códigos vacío o igual al anterior se detecta en el primer uso, no al arrancar.
- Los mensajes del comando están marcados para traducción, pero `makemessages` no se ha ejecutado
  (falta `gettext` en el entorno).
- Nada programa la purga; hasta entonces los caducados solo se borran al repetir el mismo correo.
- **Tiempo de respuesta igual por construcción, no medido**: `start`, `verify`, `resend` y
  `complete` hacen las mismas consultas con plaza o con registro real (los tests lo fijan), pero
  ningún test mide tiempos reales.
- **Equivalencia probada en las secuencias conocidas, no en todas**: los tests comparan plaza y
  registro real en los recorridos de bloqueo, caducidad, reenvío, repetición, resolución retrasada,
  peticiones desordenadas y operación simultánea. Una secuencia que nadie ha pensado podría
  distinguirlos todavía.
- Si la cola tarda más de `REGISTRATION_START_RETRY_MINUTES` en atender la tarea, el registro no
  llega a crearse y no se envía correo: hay que volver a empezar.
- Si se pierde el encolado de un reenvío, el proceso se queda sin código válido hasta que se pida
  otro reenvío: `reissue_code` no tiene barrido.
- Sin el worker de Celery en marcha, ningún registro recibe su código.

## Cómo probarlo
Requisitos: Docker y `main` actualizado. En el VPS sigue *Actualizar* y *Migraciones* de la sección
*Entorno remoto* del README. Todos los comandos se ejecutan desde la raíz del repositorio. Sin
proveedor de correo configurado, los correos salen por la consola del worker: ahí se lee el código.

1. Levanta la base de datos y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   Aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver, entre otras, `accounts.0008_phantomprocess... OK`. Levanta el worker y el
   planificador de Celery:
   ```bash
   docker compose -f docker/docker-compose.yml up -d worker beat
   ```
2. Inicia un registro:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email Ana@Example.com --name "Ana García" --birthdate 1990-05-10 --country es --language es
   ```
   Verás una sola línea, `public_id: …`. Anótala: en los pasos siguientes, `<PUBLIC_ID>` es ese
   valor. Con `--country XX` o `--birthdate 2020-01-01` verás el error de ese campo.
3. Lee el código en la salida del worker:
   ```bash
   docker compose -f docker/docker-compose.yml logs worker --tail 60
   ```
   Deberías ver el correo «Confirma tu correo para crear tu cuenta» con un código de 6 dígitos y un
   enlace que termina en `#<PUBLIC_ID>`. Si aún no aparece, espera unos segundos y repite. Desde
   aquí, `<CODE>` es ese código.
4. Prueba un código erróneo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> 000000
   ```
   Deberías ver `Wrong code.`
5. Pide un código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration resend <PUBLIC_ID>
   ```
   Verás solo el mismo `public_id`. Repite el comando del paso 3: el correo más reciente trae otro
   código, y desde aquí `<CODE>` es el nuevo. El código anterior ya no sirve.
6. Verifica el código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
   ```
   Deberías ver `Code verified.`
7. Completa el registro. Primero con una contraseña débil, para ver cada regla incumplida:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID> --password 12345678
   ```
   Después sin `--password`. Te pedirá la contraseña sin mostrarla; usa 12 caracteres o más:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID>
   ```
   Verás `account: ana@example.com`.
8. Repite el comando del paso 2 con el mismo correo. La respuesta es igual que la primera vez: una
   línea `public_id: …` con otro valor; en los pasos siguientes, `<OTHER_ID>` es ese valor. Repite
   el comando del paso 3: esta vez llega el aviso «Ya tienes una cuenta con este correo», sin
   código. Ese identificador no tiene registro detrás, pero responde como uno real:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <OTHER_ID> 000000
   ```
   Deberías ver `Wrong code.`; tras cinco intentos, el bloqueo, igual que en un registro real.
9. Comprueba que la cuenta inicia sesión. `<PASSWORD>` es la contraseña que fijaste en el paso 7:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from django.test import Client; print(Client().post('/_allauth/app/v1/auth/login', data={'email': 'ana@example.com', 'password': '<PASSWORD>'}, content_type='application/json', HTTP_HOST='localhost').status_code)"
   ```
   Debe imprimir `200`.
10. Purga los caducados:
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration purge
    ```
    Verás `deleted: N`, que suma registros pendientes y plazas.
11. Ejecuta la suite completa (cobertura mínima 80 % sobre todo el proyecto):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend pytest -q
    ```

## Marco teórico
### Huella del código (HMAC)
Guardar el código tal cual permitiría usarlo a quien lea la base de datos. Un hash simple
tampoco basta: con solo un millón de códigos posibles se prueban todos en segundos. El HMAC mezcla
el código con un secreto que no está en la base de datos, así que sin ese secreto la huella no
sirve. Atarla al `public_id` impide reutilizarla en otro proceso.

Desde `huellas-hmac-unificadas`, esta huella se calcula y se comprueba en
`backend/apps/core/fingerprints.py` (`code_fingerprint` / `code_matches`), el único sitio del
backend que calcula huellas con clave; el formato y el secreto no cambiaron.

### Rotación del secreto
Cambiar el secreto invalidaría todos los códigos en curso. Durante un periodo de transición se
acepta también el anterior; como un proceso vive como mucho 1 hora, basta con una hora de solape.

### Enumeración de cuentas
Si el sistema responde distinto según exista o no una cuenta, un atacante puede averiguar qué
correos están registrados. Por eso se validan primero los datos y solo después se mira si hay
cuenta: con datos inválidos la respuesta es la misma en ambos casos.

### Enumeración por tiempo de respuesta
Aunque el texto de la respuesta sea idéntico, si con cuenta se tarda 5 ms y sin ella 80 ms (porque
solo en un caso se genera el código y se escribe el correo), midiendo el tiempo se distingue un
caso del otro. Por eso la respuesta hace siempre el mismo trabajo (validar y guardar una plaza) y
todo lo que depende de la cuenta se hace después, en segundo plano.

### Plaza e identificador sin registro detrás
La plaza es una fila con un `public_id` que se guarda en la respuesta para cualquier solicitud
válida. Si el correo no tiene cuenta, se convierte en el registro pendiente; si la tiene, se queda
como identificador "vacío": no acepta ningún código, pero cuenta intentos, se bloquea y caduca
igual que un registro real. Quien lo use no puede saber si detrás hay un registro.

### Trabajo fuera de la respuesta y barrido
Celery ejecuta tareas en un proceso aparte (el worker) a partir de mensajes en Redis. La tarea se
encola solo cuando la transacción se confirma (`on_commit`), para no procesar una plaza que no
llegó a guardarse. Si Redis no responde en ese momento, la respuesta no cambia: un barrido
programado cada 60 s vuelve a encolar las plazas pendientes.

### Fallo abierto (fail-open)
Si el servicio de contraseñas filtradas no responde, se acepta la contraseña en lugar de bloquear
el registro. Se gana disponibilidad a cambio de que, mientras el servicio esté caído, pueda pasar
una contraseña filtrada.

### Consultar contraseñas filtradas sin revelarlas (k-anonimato)
Solo se envían los 5 primeros caracteres de la huella SHA-1 de la contraseña; el servicio devuelve
cientos de huellas que empiezan igual y la comparación se hace en nuestro servidor. El servicio
nunca sabe qué contraseña se consultó.

### Código validado frente a registro completado
"Validado" significa que el código fue correcto: el registro pendiente sigue existiendo y espera
la contraseña. "Completado" significa que la cuenta ya existe y el registro pendiente se borró.

### Condiciones de carrera y bloqueo de fila
Si dos peticiones leen "0 intentos" a la vez, ambas creen tener intentos libres. Bloquear la fila
(`select_for_update`) obliga a la segunda a esperar a que la primera guarde su intento.
