# Tareas: usuario-personalizado
Estado: aprobado

Rutas relativas a `backend/apps/accounts/` salvo que se indique. "Suite verde" =
`cd backend && pytest -q` + `mypy .` + `ruff check .` + `black --check .` sin errores.

- [x] T-001 Validadores de nombre, fecha de nacimiento y país
  RF: RF-003, RF-004, RF-005 | Depende de: — | Archivos: 3
  Archivos: `backend/requirements.txt` (`pycountry`), `validators.py`, `tests/test_validators.py`.
  Hecho cuando: `pytest apps/accounts/tests/test_validators.py -q` pasa: nombre (vacío, >150, doble
  espacio, tabulador, salto de línea, tildes y otros alfabetos); edad (un día antes y el día
  exacto de 18 años + 5 días, 29-feb → 5-mar en año no bisiesto, fecha futura); país (`es` → `ES`,
  `XX`, `XK`, `ZZ` nuevo rechazado, `ZZ` conservado aceptado); suite verde.

- [x] T-002 Creación centralizada de usuarios en los tests de auth-headless
  RF: — (S-08, CF-4) | Depende de: — | Archivos: 3
  Archivos: `tests/factories.py` (`make_user`), `tests/conftest.py`, `tests/test_user_model.py`.
  Hecho cuando: ningún test de `apps/accounts/tests/` fuera del spike llama a `create_user` salvo
  los que prueban el propio manager; `make_user` es el único punto de creación; suite verde.

- [x] T-003 Adapter de test del spike que completa el perfil en el signup
  RF: — (S-08, CF-4) | Depende de: T-002 | Archivos: 3
  Archivos: `tests/spike_allauth/adapters.py` (`ProfileFillingAdapter` y variantes que heredan de
  él), `tests/spike_allauth/conftest.py` (lo activa por defecto), `tests/spike_allauth/test_late_entry.py`
  (control con `make_user`).
  Hecho cuando: los 26 tests del spike pasan sin cambiar ninguna aserción de caracterización;
  suite verde.

- [x] T-004 Campos obligatorios name, birthdate y country con relleno
  RF: RF-006, RF-011 (relleno) | Depende de: T-001, T-002, T-003 | Archivos: 5
  Archivos: `models.py` (campos, `REQUIRED_FIELDS`), `migrations/0002_…` (`AddField` con relleno),
  `tests/factories.py` (valores por defecto), `management/commands/seed_test_user.py`,
  `tests/test_user_model.py` (obligatoriedad y `createsuperuser --noinput`).
  Hecho cuando: `python manage.py migrate` aplica `0002`; crear un usuario sin alguno de los tres
  campos falla; `createsuperuser --noinput` con los tres crea la cuenta; suite verde.
  Excepción: los campos obligatorios, su migración, la factoría y el seed tienen que cambiar juntos;
  separados, la suite queda en rojo entre tareas.

- [x] T-005 Correo normalizado y único sin distinguir mayúsculas
  RF: RF-001, RF-002 | Depende de: T-004 | Archivos: 3
  Archivos: `models.py` (normalización en `save()`, `UniqueConstraint(Lower("email"))`),
  `migrations/0003_…` (normaliza correos existentes, aborta si chocan, crea la restricción),
  `tests/test_user_model.py`.
  Hecho cuando: "Ana@x.com" y "ana@x.com" chocan por `create_user`, por `save()` directo y por
  `bulk_create` sin normalizar (`IntegrityError`); " Ana@X.com " se guarda como "ana@x.com";
  también choca contra una cuenta inactiva; suite verde. (CF-2)

- [x] T-006 Migración sobre datos existentes
  RF: RF-011 | Depende de: T-005 | Archivos: 1
  Archivos: `tests/test_migrations.py`.
  Hecho cuando: con `MigrationExecutor`, migrar a `0001`, crear cuentas, migrar a la última y
  comprobar el relleno ("Usuario sin nombre", 1900-01-01, `ZZ`) y los correos en minúsculas; con
  dos correos que solo difieren en mayúsculas, la migración falla con un mensaje que los nombra;
  suite verde. (CF-1)

- [x] T-007 Validación en todo guardado normal
  RF: RF-003, RF-004, RF-005, RF-006 | Depende de: T-005 | Archivos: 2
  Archivos: `models.py` (`save()` con `full_clean`; con `update_fields`, solo esos campos; excepción
  `ZZ`), `tests/test_user_model.py`.
  Hecho cuando: `save()`, `create_user` y `createsuperuser` rechazan nombre, edad o país inválidos;
  una cuenta con relleno `ZZ` puede guardar `last_login` y cambiar su nombre, pero no poner `ZZ` de
  nuevo tras cambiar el país; suite verde.

- [x] T-008 Cuenta inactiva (borrado lógico) y atributos de administración
  RF: RF-007, RF-008 | Depende de: T-007 | Archivos: 3
  Archivos: `models.py` (gestor `active`), `tests/test_user_model.py` (valores por defecto,
  `User.active` excluye inactivas, `User.objects` las incluye), `tests/test_inactive_login.py`.
  Hecho cuando: una cuenta inactiva no puede iniciar sesión por browser ni por app y reactivarla lo
  permite de nuevo; suite verde.

- [x] T-009 Configuración del historial
  RF: RF-009 | Depende de: — | Archivos: 3
  Archivos: `backend/requirements.txt` (`django-simple-history`), `backend/config/settings.py`
  (`INSTALLED_APPS` y `HistoryRequestMiddleware`), `backend/pyproject.toml` (excepción de mypy).
  Hecho cuando: `python manage.py check` no da errores con la app instalada; suite verde.

- [x] T-010 Historial de User
  RF: RF-009, RF-010 | Depende de: T-008, T-009 | Archivos: 3
  Archivos: `models.py` (`HistoricalRecords` sin `password` ni `last_login`; sin versión si solo
  cambia `last_login`), `migrations/0004_…`, `tests/test_user_history.py`.
  Hecho cuando: alta, cambio y borrado físico crean versiones sin `password` ni `last_login`, con
  autor en una petición autenticada y vacío por consola; el historial sobrevive al borrado; iniciar
  sesión no crea versión; suite verde.

- [x] T-011 Resumen de la feature
  RF: todos (documentación) | Depende de: T-001…T-010 | Archivos: 1
  Archivos: `specs/usuario-personalizado/resumen.md`.
  Hecho cuando: el resumen contiene qué se hizo, cómo probarlo (incluidos `migrate` y
  `createsuperuser`) y el marco teórico de los conceptos que generaron dudas.

- [x] T-012 Corrección: tests de normalización del correo al modificar y conservación de puntos y +etiqueta
  Tipo: corrección | Origen: validación de RF-001
  RF: RF-001 | Depende de: — | Archivos: 1
  Archivos: `tests/test_user_model.py`.
  Causa: ningún test modifica el correo de un usuario existente ni usa puntos o `+etiqueta`; los
  mutantes "normalizar solo al crear" y "quitar la +etiqueta" sobreviven.
  Hecho cuando: un test crea `" Ana.B+Tag@X.com "` y comprueba `"ana.b+tag@x.com"`; otro modifica
  el correo de un usuario existente por `save()` y comprueba que se guarda normalizado; ambos
  mutantes hacen fallar la suite; la suite completa sigue en verde.

- [x] T-013 Corrección: test de obligatoriedad de nombre, fecha y país en el guardado directo del modelo
  Tipo: corrección | Origen: validación de RF-006
  RF: RF-006 | Depende de: — | Archivos: 1
  Archivos: `tests/test_user_model.py`.
  Causa: la obligatoriedad solo se prueba por `create_user` y `createsuperuser`; `models.py:117-118`
  sin cubrir; los mutantes "rellenar en silencio" y "omitir `super().clean_fields()`" sobreviven.
  Hecho cuando: un test parametrizado comprueba que `User(email=..., <sin un campo>).save()` lanza
  `ValidationError` con ese campo en `error_dict` y no crea la cuenta; las líneas 117-118 quedan
  cubiertas; la suite completa sigue en verde.

- [ ] T-014 Corrección: test de que desactivar una cuenta activa conserva sus datos
  Tipo: corrección | Origen: validación de RF-007
  RF: RF-007 | Depende de: — | Archivos: 1
  Archivos: `tests/test_inactive_login.py`.
  Causa: ningún test pasa una cuenta de activa a inactiva; el mutante "anonimizar al desactivar"
  sobrevive.
  Hecho cuando: un test crea una cuenta activa, la desactiva por `save()`, comprueba que correo,
  nombre, fecha y país no cambian y que no puede iniciar sesión, y después la reactiva e inicia
  sesión con las mismas credenciales (browser y app); la suite completa sigue en verde.

- [ ] T-015 Corrección: tests del contenido completo del historial y del autor en una petición real
  Tipo: corrección | Origen: validación de RF-009
  RF: RF-009 | Depende de: — | Archivos: 1-2
  Archivos: `tests/test_user_history.py` y, si hace falta, un módulo de URLs de test.
  Causa: el test de campos comprueba un subconjunto y el test de autor invoca el middleware a mano;
  los mutantes "excluir más campos del historial" y "quitar `HistoryRequestMiddleware`" sobreviven.
  Hecho cuando: el historial contiene exactamente los campos concretos de `User` salvo `password` y
  `last_login`; una versión `~` contiene los datos modificados y `history_date`; un cambio hecho en
  una petición real (con `Client` y el `MIDDLEWARE` de settings) registra `history_user`; ambos
  mutantes hacen fallar la suite; la suite completa sigue en verde.

## RF sin tarea
Ninguno.
