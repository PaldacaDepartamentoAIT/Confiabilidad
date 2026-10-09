# Resumen — procesos-pendientes
Estado: cerrada con riesgo residual aceptado (3.ª ronda de correcciones) · Última actualización: 2026-10-07

## Qué se hizo
El registro pasa por un **registro pendiente**: la cuenta no existe hasta que se demuestra el
acceso al correo con un código y se fija una contraseña. Todo se puede recorrer desde consola con
`manage.py registration`, sin frontend ni API (RF-023). La API será la feature siguiente y usará el
mismo servicio (`apps/accounts/registration.py`).

- **Registro pendiente** (`PendingRegistration`, migración `0005`): correo, nombre, fecha de
  nacimiento y país, validados con las mismas reglas que la cuenta; un solo registro por correo sin
  distinguir mayúsculas y `public_id` único, garantizados por la base de datos (RF-001…RF-004).
- **Código de 6 dígitos** vigente 15 min. Solo se guarda su huella (HMAC con un secreto del
  servidor y atada al `public_id`); el código en claro se entrega una vez (RF-007, RF-008). El
  secreto se puede rotar sin invalidar los códigos en curso (RF-015).
- **Verificación**: 5 intentos fallidos bloquean el código hasta pedir otro (RF-009, RF-010).
- **Caducidad**: el proceso muere 15 min después de caducar su código o 1 h después del alta, lo
  que llegue antes (RF-011). La gracia sirve para completar tras validar el código.
- **Reenvío**: mismo `public_id`, código nuevo, intentos a 0 (RF-016).
- **Registro repetido** con un registro vigente: conserva los datos, emite `public_id` y código
  nuevos y anula la validación, para que nadie se apropie de un registro ajeno (RF-005, S-06).
- **Completar**: crea la cuenta con el correo verificado y borra el registro, todo o nada; si el
  correo consiguió cuenta entretanto, rechaza y borra el registro (RF-012, RF-020).
- **Política de contraseñas** de todo el proyecto: 12 caracteres o más, no parecida al correo ni
  al nombre, no común y no filtrada según Have I Been Pwned, consultado sin enviar la contraseña.
  Si el servicio no responde, se acepta y se registra un aviso (RF-022, S-09).
- **Limpieza**: `registration purge` borra los procesos caducados (RF-013).
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
- La concurrencia (dos verificaciones o dos altas a la vez) está protegida con bloqueos de fila,
  pero ningún test la ejerce con transacciones reales.
- Si otra vía crea la cuenta justo entre la comprobación y el alta en `complete`, sale un
  `IntegrityError` sin traducir y el registro pendiente se conserva, en vez de borrarse, hasta el
  siguiente intento; la base de datos impide el duplicado igualmente. Hay que traducirlo antes de
  la API (anotado en `HUMAN_TODO.md`).
- Un secreto de códigos vacío o igual al anterior se detecta en el primer uso, no al arrancar.
- Los mensajes del comando están marcados para traducción, pero `makemessages` no se ha ejecutado
  (falta `gettext` en el entorno).
- Nada programa la purga; hasta entonces los caducados solo se borran al repetir el mismo correo.

## Cómo probarlo
Requisitos: Docker y `main` actualizado (la feature ya está fusionada). En el VPS sigue *Actualizar* y
*Migraciones* de la sección *Entorno remoto* del README. Todos los comandos se ejecutan desde la
raíz del repositorio.

1. Levanta la base de datos y Redis:
   ```bash
   docker compose -f docker/docker-compose.yml up -d db redis
   ```
   Aplica las migraciones:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate
   ```
   Deberías ver `accounts.0005_pendingregistration... OK`.
2. Inicia un registro:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration start --email Ana@Example.com --name "Ana García" --birthdate 1990-05-10 --country es
   ```
   Verás dos líneas, `public_id: …` y `code: …` (6 dígitos). Anótalas: en los pasos siguientes,
   `<PUBLIC_ID>` y `<CODE>` son esos valores. Con `--country XX` o `--birthdate 2020-01-01` verás
   el error de ese campo.
3. Prueba un código erróneo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> 000000
   ```
   Deberías ver `Wrong code.`
4. Pide un código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration resend <PUBLIC_ID>
   ```
   Verás el mismo `public_id` y otro `code`: desde aquí, `<CODE>` es el nuevo.
5. Verifica el código nuevo:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration verify <PUBLIC_ID> <CODE>
   ```
   Deberías ver `Code verified.`
6. Completa el registro. Primero con una contraseña débil, para ver cada regla incumplida:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID> --password 12345678
   ```
   Después sin `--password`. Te pedirá la contraseña sin mostrarla; usa 12 caracteres o más:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration complete <PUBLIC_ID>
   ```
   Verás `account: ana@example.com`.
7. Repite el comando del paso 2: ahora responde `An account with this email already exists.`
8. Comprueba que la cuenta inicia sesión. `<PASSWORD>` es la contraseña que fijaste en el paso 6:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from django.test import Client; print(Client().post('/_allauth/app/v1/auth/login', data={'email': 'ana@example.com', 'password': '<PASSWORD>'}, content_type='application/json', HTTP_HOST='localhost').status_code)"
   ```
   Debe imprimir `200`.
9. Purga los caducados:
   ```bash
   docker compose -f docker/docker-compose.yml run --rm backend python manage.py registration purge
   ```
   Verás `deleted: N`.
10. Ejecuta la suite completa (cobertura mínima 80 % sobre todo el proyecto):
    ```bash
    docker compose -f docker/docker-compose.yml run --rm backend pytest -q
    ```

## Marco teórico
### Huella del código (HMAC)
Guardar el código tal cual permitiría usarlo a quien lea la base de datos. Un hash simple
tampoco basta: con solo un millón de códigos posibles se prueban todos en segundos. El HMAC mezcla
el código con un secreto que no está en la base de datos, así que sin ese secreto la huella no
sirve. Atarla al `public_id` impide reutilizarla en otro proceso.

### Rotación del secreto
Cambiar el secreto invalidaría todos los códigos en curso. Durante un periodo de transición se
acepta también el anterior; como un proceso vive como mucho 1 hora, basta con una hora de solape.

### Enumeración de cuentas
Si el sistema responde distinto según exista o no una cuenta, un atacante puede averiguar qué
correos están registrados. Por eso se validan primero los datos y solo después se mira si hay
cuenta: con datos inválidos la respuesta es la misma en ambos casos.

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
