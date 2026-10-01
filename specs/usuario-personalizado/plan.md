# Plan: usuario-personalizado
Estado: aprobado

## Módulos

### M-01 Modelo `User` (`apps/accounts/models.py`)
Responsabilidad: campos `name`, `birthdate`, `country`; `save()` que normaliza (correo, nombre,
país) y valida (M-02) antes de guardar; gestor `objects` (todas las cuentas) y gestor `active`
(solo activas); `REQUIRED_FIELDS = ["name", "birthdate", "country"]` para `createsuperuser`;
restricción de unicidad del correo sin distinguir mayúsculas; historial (M-04).
RF: RF-001…RF-008

### M-02 Validadores (`apps/accounts/validators.py`)
Responsabilidad: funciones puras para nombre (sin espacios dobles ni caracteres de control, ≤150),
fecha de nacimiento (no futura; 18 años + 5 días, 29-feb → 28-feb) y país (lista ISO vigente,
excepción `ZZ` sin cambios).
RF: RF-003, RF-004, RF-005

### M-03 Migraciones (`apps/accounts/migrations/`)
Responsabilidad: `0002` añade los campos con el relleno de RF-011, normaliza los correos
existentes, aborta con un mensaje claro si hay correos que solo difieren en mayúsculas y crea la
restricción de unicidad; `0003` crea la tabla de historial.
RF: RF-002, RF-011

### M-04 Historial (configuración)
Responsabilidad: `django-simple-history` (`INSTALLED_APPS` y `HistoryRequestMiddleware` para saber
quién hizo el cambio en peticiones web), excluyendo `password` y `last_login`.
RF: RF-009, RF-010

### M-05 Comando `seed_test_user`
Responsabilidad: crear el usuario de prueba con nombre, fecha y país válidos.
RF: RF-006

### M-06 Utilidades de test
Responsabilidad: `apps/accounts/tests/factories.py` con `make_user(**cambios)`; en el spike, un
adapter base `ProfileFillingAdapter` que completa nombre, fecha y país en el signup, del que heredan
las variantes (`DeferredSaveAdapter`, etc.). Todos los tests existentes pasan a usarlos (S-08).
RF: CF-4

## Modelo de datos
`accounts.User` (hereda de `AbstractBaseUser` y `PermissionsMixin`):
- `email` EmailField, único (se mantiene) + `UniqueConstraint(Lower("email"))`.
- `name` CharField(150), `birthdate` DateField, `country` CharField(2) — obligatorios.
- `is_active` (por defecto `True`), `is_staff` (por defecto `False`), `date_joined`
  (al crear), `password`, `last_login`, `is_superuser` — heredados o ya existentes.
`HistoricalUser` (generado): los mismos campos salvo `password` y `last_login`, más
`history_id`, `history_date`, `history_type` (+ / ~ / -) y `history_user` (nulo si se desconoce).

## Decisiones

### D-01 Unicidad del correo sin distinguir mayúsculas
Elegida: restricción única sobre `Lower(email)`, además del `unique=True` del campo.
Descartada: tipo `citext` o una colación no determinista de Postgres.
Motivo: la restricción funcional la impone la base de datos en cualquier vía (RF-002) sin
extensiones; `unique=True` se mantiene porque Django lo exige al campo de login (check `auth.E003`).

### D-02 Dónde se valida
Elegida: `save()` del modelo llama a la validación completa (`full_clean`).
Descartada: validar solo en formularios o serializadores.
Motivo: la spec exige las reglas en todo guardado normal: consola, código y allauth incluidos.

### D-03 Guardados parciales
Elegida: si `save()` recibe `update_fields`, normaliza y valida solo esos campos.
Descartada: validar todo en cada guardado.
Motivo: el login guarda solo `last_login`; validarlo todo haría fallar el login de las cuentas de
relleno (`ZZ`) y repetiría comprobaciones que no cambian.

### D-04 Excepción del relleno `ZZ`
Elegida: el validador de país admite `ZZ` solo si la cuenta ya existe y su país guardado es `ZZ`.
Descartada: un campo extra "es relleno".
Motivo: no añade columnas y cumple "se conserva mientras no se cambie el país" (RF-005).

### D-05 Cálculo de la edad
Elegida: fecha del 18.º cumpleaños (29-feb → 28-feb en años no bisiestos) + 5 días, comparada con la
fecha local del servidor.
Descartada: restar 18 × 365 días.
Motivo: los años bisiestos desplazan el resultado varios días.

### D-06 Lista ISO 3166-1
Elegida: `pycountry` (dependencia nueva, aprobada por el usuario el 2026-09-29).
Descartada: `django-countries` (más pesada: campo propio, traducciones, admin) o una lista fija en
el código (no se actualiza sola).
Motivo: `pycountry` sigue la lista oficial (249 códigos, sin `XK` ni `ZZ`) y está tipada.

### D-07 Cuentas inactivas y consultas "normales"
Elegida: el gestor por defecto `objects` devuelve todas las cuentas y el gestor `active` solo las
activas; las consultas de la aplicación usan `User.active`. El login de las inactivas ya lo
rechazan Django y allauth. (Aprobada por el usuario el 2026-09-29.)
Descartada: que el gestor por defecto oculte las inactivas.
Motivo: Django desaconseja filtrar el gestor por defecto. Rompe la validación de unicidad (un
correo de una cuenta inactiva no se detectaría hasta la base de datos), las búsquedas de los
backends de autenticación, `dumpdata` y el admin que deberá reactivarlas.
Riesgo: la exclusión es por convención. Un código nuevo que use `objects` verá las inactivas.

### D-08 Historial solo de datos rastreados
Elegida: no registrar versión cuando el guardado solo toca campos excluidos (`last_login`).
Descartada: una versión por cada guardado.
Motivo: si no, cada inicio de sesión crearía una versión idéntica a la anterior.

### D-09 Migración de datos
Elegida: `AddField` con el relleno como valor por defecto, que luego se retira
(`preserve_default=False`); un paso de datos pasa los correos a minúsculas y aborta si hay
colisiones antes de crear la restricción.
Descartada: borrar la base de datos de desarrollo.
Motivo: RF-011 exige conservar las cuentas y fallar sin fusionar.

### D-10 Utilidades de test centralizadas
Elegida: `make_user` y `ProfileFillingAdapter` (S-08).
Descartada: añadir los campos a mano en cada test.
Motivo: un campo obligatorio nuevo solo obliga a tocar dos puntos.

## Estrategia de tests
- **Unitario** (`test_validators.py`): nombre, edad (límite exacto, 29-feb, fecha futura) y país
  (válido, `XX`, `XK`, `ZZ` nuevo o conservado) → RF-003…RF-005.
- **Modelo** (`test_user_model.py`): normalización (RF-001); "Ana@x.com" contra "ana@x.com" por
  `create_user`, por `save()` directo y por `bulk_create` o `update()` sin normalizar, que choca en
  la base de datos (RF-002, CF-2); obligatoriedad y `createsuperuser --noinput` (RF-006); valores
  por defecto y gestor `active` (RF-007, RF-008).
- **Integración**: una cuenta inactiva no puede iniciar sesión por browser ni por app (RF-007).
- **Historial** (`test_user_history.py`): alta, cambio y borrado registrados sin `password` ni
  `last_login`, con autor; conservación tras el borrado; el login no crea versión (RF-009,
  RF-010, D-08).
- **Migración** (`test_migration_0002.py`): con `MigrationExecutor` (sin dependencia nueva):
  migrar a `0001`, insertar cuentas, migrar hacia delante y comprobar el relleno; con correos que
  chocan, la migración falla (RF-011, CF-1).
- Los tests existentes (`auth-headless` y el spike) pasan a usar las utilidades de M-06 (CF-4).
- `mypy`: excepción de `simple_history.*` en `pyproject.toml`, igual que `allauth.*`.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01 | modelo |
| RF-002 | M-01, M-03 | modelo (incl. escritura sin normalizar) + migración |
| RF-003 | M-02, M-01 | unitario + modelo |
| RF-004 | M-02, M-01 | unitario + modelo |
| RF-005 | M-02, M-01 | unitario + modelo |
| RF-006 | M-01, M-05 | modelo + comando |
| RF-007 | M-01 | modelo + integración (login) |
| RF-008 | M-01 | modelo |
| RF-009 | M-04 | historial |
| RF-010 | M-04 | historial |
| RF-011 | M-03 | migración |

## RF sin cobertura
Ninguno.
