# HUMAN_TODO — procesos-pendientes

Acciones que **requieren intervención humana** para completar la feature `procesos-pendientes`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Definir `REGISTRATION_CODE_SECRET` en producción, cifrado con SOPS** (features
  `procesos-pendientes` y `cambio-contrasena`). Protege las huellas de los códigos de registro y
  de cambio de contraseña: sin él, cualquiera con la base de datos podría probar el millón de
  códigos posibles (RF-008) y, con un código de cambio de contraseña en curso, tomar la cuenta. Si
  no se define, se usa `DJANGO_SECRET_KEY`, lo que ata su rotación a la de las sesiones. Genera uno
  propio:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Añade el valor que imprime como `REGISTRATION_CODE_SECRET` en el archivo cifrado:
  ```bash
  sops secrets/prod.enc.yaml
  ```
  Para rotarlo sin invalidar los códigos en curso (RF-015): pasa el valor actual a
  `REGISTRATION_CODE_SECRET_PREVIOUS`, pon el nuevo en `REGISTRATION_CODE_SECRET` y la hora del
  cambio en `REGISTRATION_CODE_SECRET_ROTATED_AT` (ISO 8601 con zona, p. ej.
  `2026-10-06T10:00:00+00:00`). El anterior vale durante `REGISTRATION_SECRET_TRANSITION_MINUTES`
  (60 por defecto); después puedes borrar las dos variables de rotación.

- [ ] **Limitar la frecuencia del reenvío de códigos antes de publicar la API de registro**
  (feature `procesos-pendientes`, S-07). Cada reenvío reinicia los intentos, así que el tope de 5
  intentos es por código, no por proceso: sin límite de reenvíos, un atacante puede probar códigos
  sin parar durante la hora de vida del registro. En consola no hay riesgo; decide el límite (por
  correo y por IP) al especificar la feature de la API.

- [ ] **Traducir el `IntegrityError` de `complete` antes de publicar la API de registro**
  (feature `procesos-pendientes`, riesgo residual). Si otra vía crea la cuenta justo entre la
  comprobación y el alta, `registration.complete` lanza `IntegrityError`: en la API sería un
  error 500 y el registro pendiente se conservaría en vez de borrarse (RF-012). Debe devolver
  "cuenta existente" y borrar el registro.

- [ ] **Probar una vez el validador de contraseñas filtradas con red real** (feature
  `procesos-pendientes`, riesgo residual). En el entorno remoto no hay salida a
  `api.pwnedpasswords.com` y los tests lo simulan. En tu máquina, en `registration complete`
  prueba una contraseña filtrada conocida de 12+ caracteres (por ejemplo `password1234`): debe
  rechazarse con "appeared in a data breach". Si sale el aviso "Pwned Passwords check skipped",
  no hay salida al servicio.

## Hecho

<!-- Mueve aquí las tareas completadas, con fecha. -->
