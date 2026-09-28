# Resumen — allauth-verificacion-codigo
Estado: terminado (pendiente de validar) · Última actualización: 2026-09-28
Tipo: spike · Versiones probadas: django-allauth 65.19.4 y 65.19.5

## Respuesta corta
- **Q1 — ¿allauth tolera que el usuario no exista hasta verificar el correo?** **No.**
- **Q2 — ¿allauth permite que el código no se consuma al validarlo?** **No.** Además, el código
  solo vale en la sesión (navegador o token) que lo pidió.
- **D-01:** el registro va **fuera** de allauth (registro pendiente propio); el usuario se crea
  **a través de allauth** al fijar la contraseña, y el inicio de sesión y las sesiones se quedan
  **dentro** de allauth.

## Evidencia (cada fila es un test en `backend/apps/accounts/tests/spike_allauth/`, en browser y app)
| RF | Pregunta | Observado | Test |
|---|---|---|---|
| RF-001 | Q1 | El signup crea la fila de usuario antes de validar el código (`401`, `verify_email` pendiente). | `test_signup_creates_user_before_code_is_verified` |
| RF-002 | Q1 | Para un correo desconocido, la respuesta es idéntica a la de uno conocido, pero solo llega un correo "Unknown Account" sin código y no se crea usuario. | `test_code_request_for_unknown_email_sends_no_code` |
| RF-002 | Q1 | Confirmar un código en ese flujo: `400 incorrect_code`, sin usuario. | `test_confirming_code_for_unknown_email_creates_no_user` |
| RF-003 | Q2 | Segunda validación en la misma sesión: `409` (tras la primera ya hay sesión iniciada y no queda verificación pendiente). | `test_second_validation_in_same_session_is_rejected` |
| RF-004 | Q2 | Desde otra sesión, antes de validar: `409` y el correo sigue sin verificar; la sesión original sí puede validar después. | `test_code_from_another_session_is_rejected_before_validation` |
| RF-004 | Q2 | Desde otra sesión, después de validar: `409`. | `test_code_from_another_session_is_rejected_after_validation` |
| RF-008 | — | Reenvío inmediato: `429` (límite de 1 cada 10 s por correo); el código anterior sigue valiendo. | `test_immediate_resend_is_rate_limited_and_keeps_old_code` |
| RF-008 | — | Reenvío permitido: llega un código nuevo y el anterior se rechaza (`400 incorrect_code`). | `test_resend_invalidates_old_code_and_issues_new_one` |
| RF-005 | D-01 | Usuario creado desde un registro pendiente vía allauth: inicia sesión (`200`) y la sesión lo devuelve. | `test_user_converted_through_allauth_can_log_in` |
| RF-005 | control | Usuario sin correo verificado: `401` con `verify_email` pendiente (la verificación obligatoria está activa). | `test_user_without_verified_email_cannot_log_in` |

### Variantes "config + adapter" intentadas (RF-007)
| Pregunta | Variante | Resultado |
|---|---|---|
| Q1 | `save_user(commit=False)`: no guardar el usuario en el signup | El signup revienta (`ValueError … unsaved related object 'user'`; en producción, un 500). |
| Q1 | `is_email_verified → True`: dar el correo por verificado | Crea el usuario verificado y con sesión, sin enviar código: lo contrario de lo buscado. |
| Q2 | `generate_email_verification_code` fijo | Mismo comportamiento que el código aleatorio: lo que manda es el estado en la sesión. |
| Q2 | Resto de métodos públicos del adapter | Ninguno decide dónde se guarda el estado pendiente ni cuándo se consume (revisado en 65.19.4). |

Excepción aceptada a RF-007: los tests recargan `allauth.headless.urls` para activar las rutas de
login por código. Es el mismo punto de integración que usa `config/urls.py`, y se trata como
configuración, no como parte interna.

## Hallazgos
- C-12 El código de verificación está ligado a la sesión; por eso "cerré la ventana y vuelvo desde
  el enlace" no funciona con la verificación de allauth, aunque el código siguiera vigente.
- C-13 Con `HEADLESS_ONLY`, pedir un código para un correo desconocido exige
  `HEADLESS_FRONTEND_URLS['account_signup']` (el correo "Unknown Account" enlaza al registro);
  sin él, error 500.
- C-14 `confirm_email` del adapter necesita una petición con sesión y mensajes: en el registro
  definitivo debe llamarse dentro de una vista.
- C-15 **Afecta a `auth-headless`:** `ACCOUNT_RATE_LIMITS = {}` **no** desactiva los límites de
  allauth (solo `False` lo hace). Siguen activos, entre otros, 5 logins fallidos cada 5 min por
  correo y 20 registros por minuto e IP, en contra de su S-09. Ejecutar la suite más de 5 veces en
  5 minutos hace fallar sus tests de login (`too_many_login_attempts`). Pendiente de decisión.
- C-16 `django-allauth>=65` no está fijado: la instalación limpia trajo 65.19.5 durante el spike.
  Los tests de caracterización detectarán si una versión cambia este comportamiento.

## D-01 Qué va dentro y qué va fuera de allauth
- **Fuera (feature nueva de registro pendiente, S-10):** datos del registro, código propio con
  caducidad y límite de intentos, consumo **al completar** (S-01), reenvío que invalida el código
  anterior (S-09), enlace con un identificador opaco del registro pendiente (S-04),
  antienumeración y límites propios.
- **Entrada en allauth al fijar la contraseña:** `adapter.new_user` → `adapter.set_password` →
  `EmailAddress.objects.add_email` → `adapter.confirm_email` (probado en RF-005).
- **Dentro de allauth:** inicio de sesión, sesión por cookie (web) y por token (Tauri), consulta
  de sesión y cierre de sesión.
- **Por qué:** Q1 y Q2 son "no" también con el adapter, y el código atado a la sesión impide
  reanudar desde otro navegador, que es el caso central del flujo.
- **Pendiente para la feature de registro:** decidir qué hacer con el signup de allauth, que
  sigue expuesto (`/auth/signup`), para no tener dos vías de alta. No se ha probado en este spike.

## Cómo probarlo
1. Levanta la base de datos y Redis: `docker compose -f docker/docker-compose.yml up -d db redis`
2. Ejecuta los tests del spike (con el entorno del backend):
   `cd backend && pytest apps/accounts/tests/spike_allauth -v -o addopts=`
3. Deberías ver 26 tests en verde (13 casos × browser/app).
4. Si repites la suite completa más de 5 veces en 5 minutos, pueden fallar los tests de login de
   `auth-headless` por C-15; espera 5 minutos o vacía la caché de Redis.

## Marco teórico
### Código ligado a la sesión
allauth no guarda el código pendiente en la base de datos, sino en la **sesión** de quien lo
pidió (la cookie del navegador o el token de la app). Otra pestaña con otra sesión, otro navegador
o el móvil no tienen ese estado, así que el código no les sirve aunque sea correcto. Por eso un
flujo reanudable necesita guardar el estado en un sitio compartido (un registro en la base de
datos) y encontrarlo con un identificador que viaje en el enlace.

### Consumir al validar frente a consumir al completar
Un código de un solo uso se invalida en cuanto se usa. En un registro en dos pasos (código →
contraseña) eso obliga a recordar de otra forma que el código ya se confirmó. Consumirlo **al
completar** el registro permite reanudar sin pedir otro código, y no añade riesgo mientras el
código caduque: quien tiene acceso al correo ya tiene el enlace y el código.

### Por qué no se pone la sesión en una URL
Una URL acaba en el historial, en los logs del servidor y del proxy, en la cabecera `Referer` y
en correos reenviados. Si lleva la sesión, quien la vea puede **suplantar al usuario** (secuestro
de sesión). El enlace debe llevar un identificador opaco del registro pendiente que no inicie
sesión por sí mismo, caduque y se trate como un secreto.

### Enumeración de cuentas
Si la respuesta cambia según exista o no el correo, un atacante puede averiguar quién está
registrado. allauth responde igual en ambos casos y envía un correo distinto (con o sin código).
El registro propio debe mantener esa misma propiedad.

### Tests de caracterización
En vez de afirmar lo que *queremos* que haga una librería, afirman lo que *hace*. Sirven para
tomar decisiones con evidencia y para enterarse si una actualización cambia ese comportamiento:
el test falla y avisa.

### Rate limiting (límite de peticiones)
Limitar cuántas veces se puede hacer algo (registrarse, iniciar sesión, reenviar un código) en
una ventana de tiempo frena los ataques de fuerza bruta y el abuso del correo. allauth guarda los
contadores en la caché (aquí, Redis), por eso sobreviven entre tests y ejecuciones.
