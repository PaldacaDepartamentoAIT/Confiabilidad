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

- [ ] T-002 Código para un correo desconocido (browser + app)
  RF: RF-002 | Depende de: T-001 | Archivos: 3
  Archivos: `urls.py` (urlconf reconstruido tras el override), `conftest.py` (recarga del urlconf),
  `test_q1_user_existence.py`.
  Hecho cuando: el caso de RF-002 pasa afirmando si llega un código real al buzón y si validarlo
  crea el usuario, con la protección antienumeración activa; suite verde.

- [ ] T-003 Segunda validación en la misma sesión (browser + app)
  RF: RF-003 | Depende de: T-001 | Archivos: 1
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: `pytest .../test_q2_code_reuse.py -q` pasa afirmando si se acepta una segunda
  validación del mismo código en la misma sesión; suite verde.

- [ ] T-004 Validación desde otra sesión (browser + app)
  RF: RF-004 | Depende de: T-003 | Archivos: 1
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: los casos de RF-004 pasan afirmando si el código se acepta desde otra sesión,
  antes y después de una primera validación; suite verde.

- [ ] T-005 Reenvío del código (browser + app)
  RF: RF-008 | Depende de: T-003 | Archivos: 1
  Archivos: `test_q2_code_reuse.py`.
  Hecho cuando: el caso de RF-008 pasa afirmando si el código anterior se rechaza tras el reenvío
  y si llega uno nuevo; suite verde.

- [ ] T-006 Entrada tardía desde un registro pendiente (browser + app)
  RF: RF-005 | Depende de: T-001 | Archivos: 1
  Archivos: `test_late_entry.py`.
  Hecho cuando: `pytest .../test_late_entry.py -q` pasa: el registro pendiente simulado, al fijar
  la contraseña, se convierte en usuario a través de allauth (D-09) y ese usuario inicia sesión y
  aparece en la consulta de sesión en ambos clientes; suite verde.

- [ ] T-007 Variantes "config + adapter" para Q1
  RF: RF-007, RF-001 | Depende de: T-002 | Archivos: 2
  Archivos: `adapters.py`, `test_q1_user_existence.py`.
  Hecho cuando: los casos de las variantes de Q1 (`save_user` sin persistir,
  `stash_verified_email` / `is_email_verified`) pasan afirmando lo observado; suite verde.

- [ ] T-008 Variantes "config + adapter" para Q2
  RF: RF-007, RF-003, RF-004 | Depende de: T-004, T-007 | Archivos: 2
  Archivos: `adapters.py`, `test_q2_code_reuse.py`.
  Hecho cuando: se prueban los métodos públicos del adapter candidatos a controlar la invalidación
  del código, afirmando lo observado; si no hay ninguno, queda escrito en `test_q2_code_reuse.py`
  qué se revisó; suite verde.

- [ ] T-009 Informe y decisión D-01
  RF: RF-006, RF-007 | Depende de: T-001…T-008 | Archivos: 1
  Archivos: `specs/allauth-verificacion-codigo/resumen.md`.
  Hecho cuando: `resumen.md` contiene la tabla Q1/Q2 por cliente con el test que la respalda, la
  versión de allauth probada, las variantes intentadas para cada "no", D-01, el marco teórico y
  cómo reproducirlo; y `grep -rn "from allauth\|import allauth"
  backend/apps/accounts/tests/spike_allauth/` solo muestra `allauth.account.adapter`,
  `allauth.account.models` o settings.

## RF sin tarea
Ninguno.
