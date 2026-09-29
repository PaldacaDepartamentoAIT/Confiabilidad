# Tareas: allauth-verificacion-codigo
Estado: aprobado

Todas las rutas son relativas a `backend/apps/accounts/tests/spike_allauth/` salvo que se indique.
"Suite verde" = `cd backend && pytest -q` (incluida `auth-headless`) + `mypy .` + `ruff check .` +
`black --check .` sin errores.

- [x] T-001 Andamiaje del spike y existencia del usuario en el signup (browser + app)
  RF: RF-001 | Depende de: — | Archivos: 3
  Archivos: `__init__.py`, `conftest.py` (settings de verificación por test, cliente
  parametrizado browser/app, extracción del código del buzón), `test_q1_user_existence.py`.
  Hecho cuando: `pytest apps/accounts/tests/spike_allauth/test_q1_user_existence.py -q` pasa
  afirmando, para cada cliente, si existe fila de usuario antes de validar el código; suite verde.
  Incluye comprobar que la base de datos de tests está disponible en el entorno; si no, se anota
  en `HUMAN_TODO.md`.

- [x] T-002 Código para un correo desconocido (browser + app)
  RF: RF-002 | Depende de: T-001 | Archivos: 2
  Archivos: `conftest.py` (recarga de `allauth.headless.urls` y del urlconf raíz; no hay
  `urls.py` propio, ver M-02), `test_q1_user_existence.py`.
  Hecho cuando: el caso de RF-002 pasa afirmando si llega un código real al buzón y si validarlo
  crea el usuario, con la protección antienumeración activa; suite verde.

- [x] T-003 Segunda validación en la misma sesión (browser + app)
  RF: RF-003 | Depende de: T-001 | Archivos: 1
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: `pytest .../test_q2_code_reuse.py -q` pasa afirmando si se acepta una segunda
  validación del mismo código en la misma sesión; suite verde.

- [x] T-004 Validación desde otra sesión (browser + app)
  RF: RF-004 | Depende de: T-003 | Archivos: 1
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: los casos de RF-004 pasan afirmando si el código se acepta desde otra sesión,
  antes y después de una primera validación; suite verde.

- [x] T-005 Reenvío del código (browser + app)
  RF: RF-008 | Depende de: T-003 | Archivos: 1
  Excepción: se tocó también `conftest.py` para desactivar el límite de signups por IP de allauth,
  que la propia suite agota (hallazgo de esta tarea).
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: el caso de RF-008 pasa afirmando si el código anterior se rechaza tras el reenvío
  y si llega uno nuevo; suite verde.

- [x] T-006 Entrada tardía desde un registro pendiente (browser + app)
  RF: RF-005 | Depende de: T-001 | Archivos: 1
  Archivos: `test_late_entry.py`.
  Hecho cuando: `pytest .../test_late_entry.py -q` pasa: el registro pendiente simulado, al fijar
  la contraseña, se convierte en usuario a través de allauth (D-09) y ese usuario inicia sesión y
  aparece en la consulta de sesión en ambos clientes; suite verde.

- [x] T-007 Variantes "config + adapter" para Q1
  RF: RF-007, RF-001 | Depende de: T-002 | Archivos: 2
  Archivos: `adapters.py`, `test_q1_user_existence.py`.
  Hecho cuando: los casos de las variantes de Q1 (`save_user` sin persistir,
  `stash_verified_email` / `is_email_verified`) pasan afirmando lo observado; suite verde.

- [x] T-008 Variantes "config + adapter" para Q2
  RF: RF-007, RF-003, RF-004 | Depende de: T-004, T-007 | Archivos: 2
  Archivos: `adapters.py`, `test_q2_code_reuse.py`.
  Hecho cuando: se prueban los métodos públicos del adapter candidatos a controlar la invalidación
  del código, afirmando lo observado; si no hay ninguno, queda escrito en `test_q2_code_reuse.py`
  qué se revisó; suite verde.

- [x] T-009 Informe y decisión D-01
  RF: RF-006, RF-007 | Depende de: T-001…T-008 | Archivos: 1
  Archivos: `specs/allauth-verificacion-codigo/resumen.md`.
  Hecho cuando: `resumen.md` contiene la tabla Q1/Q2 por cliente con el test que la respalda, la
  versión de allauth probada, las variantes intentadas para cada "no", D-01, el marco teórico y
  cómo reproducirlo; y `grep -rn "from allauth\|import allauth"
  backend/apps/accounts/tests/spike_allauth/` solo muestra `allauth.account.adapter`,
  `allauth.account.models` o settings.

- [x] T-010 Corrección: settings probados para cada "no" en resumen.md
  Tipo: corrección | Origen: validación de RF-007
  RF: RF-007 | Depende de: — | Archivos: 1
  Archivos: `specs/allauth-verificacion-codigo/resumen.md`.
  Causa: el resumen solo enumera los métodos del adapter probados, no los settings.
  Hecho cuando: cada "no" de Q1 y Q2 en `resumen.md` lleva la lista de settings y de métodos del
  adapter probados o descartados, con el motivo; la nota de la excepción de URLs cita RF-007 en
  lugar de "excepción aceptada".

- [x] T-011 Corrección: protección antienumeración explícita en la fixture
  Tipo: corrección | Origen: validación (observación sobre M-01)
  RF: RF-002 | Depende de: — | Archivos: 1
  Archivos: `conftest.py`.
  Causa: M-01 dice que la fixture activa `ACCOUNT_PREVENT_ENUMERATION`, pero depende del valor por
  defecto de allauth.
  Hecho cuando: `spike_settings` fija `ACCOUNT_PREVENT_ENUMERATION = True`; con el valor a `False`
  (mutación) algún test de RF-002 falla; suite verde.

- [x] T-012 Corrección: anotar el hallazgo C-15 en HUMAN_TODO.md
  Tipo: corrección | Origen: validación (observación 5)
  RF: — (hallazgo C-15, afecta a auth-headless) | Depende de: — | Archivos: 1
  Archivos: `HUMAN_TODO.md`.
  Causa: `ACCOUNT_RATE_LIMITS = {}` no desactiva los límites de allauth, contra S-09 de
  `auth-headless`; requiere una decisión humana y no está anotado.
  Hecho cuando: `HUMAN_TODO.md` tiene una entrada con el problema, las dos opciones y el
  siguiente paso.

- [x] T-013 Corrección: revisión de imports ampliada y texto de T-002
  Tipo: corrección | Origen: validación de RF-007 (impacto del cambio 2026-09-29)
  RF: RF-007 | Depende de: T-011 | Archivos: 1
  Archivos: `specs/allauth-verificacion-codigo/tasks.md`.
  Causa: el grep de T-009 no detecta los imports por texto, y la línea `Archivos:` de T-002 cita
  un `urls.py` que no existe.
  Hecho cuando: `grep -rnE 'from allauth|import allauth|import_module\("allauth'
  backend/apps/accounts/tests/spike_allauth/` solo muestra `allauth.account.adapter`,
  `allauth.account.models` y `allauth.headless.urls`; la línea `Archivos:` de T-002 refleja
  `conftest.py` (recarga de URLs) y T-002 sigue marcada.

## RF sin tarea
Ninguno.
