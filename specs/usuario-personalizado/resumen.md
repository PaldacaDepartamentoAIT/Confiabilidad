# Resumen — usuario-personalizado
Estado: cerrada con riesgo residual aceptado (4.ª validación) · Última actualización: 2026-09-30

## Qué se hizo
El usuario (`accounts.User`) pasa de guardar solo el correo a tener un perfil completo, con
reglas que se cumplen en todo guardado normal y un historial auditable.

- **Nombre, fecha de nacimiento y país obligatorios** para todas las cuentas, incluidas las de
  `createsuperuser` (RF-006).
  - Nombre: sin espacios en los extremos, no vacío, máximo 150 caracteres, cualquier alfabeto;
    rechaza dos espacios seguidos, tabuladores, saltos de línea y caracteres de control (RF-003).
  - Fecha de nacimiento: no futura y con al menos 18 años y 5 días; quien nació un 29 de
    febrero cumple los 18 el 28 en años no bisiestos (RF-004).
  - País: código ISO 3166-1 alfa-2 vigente (lista de `pycountry`), guardado en mayúsculas; se
    rechazan `XX`, `XK` y `ZZ` (RF-005).
- **Correo normalizado y único sin distinguir mayúsculas** (RF-001, RF-002): se guarda sin
  espacios y en minúsculas, y la base de datos impide "Ana@x.com" y "ana@x.com" a la vez por
  cualquier vía, incluso cargas masivas o SQL directo, y aunque la otra cuenta esté inactiva.
- **Validación en todo guardado normal** (`save()`, `create_user`, `createsuperuser`, allauth).
  Un guardado parcial (`update_fields`) solo valida los campos que guarda: así el login, que
  solo guarda `last_login`, funciona aunque la cuenta tenga datos antiguos.
- **Cuenta inactiva = borrado lógico** (RF-007): no puede iniciar sesión (ni por navegador ni
  por app) y conserva todos sus datos. `User.active` devuelve solo las activas; `User.objects`,
  todas.
- **Historial** con `django-simple-history` (RF-009, RF-010): alta, cambio y borrado dejan una
  versión sin `password` ni `last_login`, con el autor si el cambio llega en una petición
  autenticada. Iniciar sesión no crea versión. El historial sobrevive al borrado físico.
- **Migraciones `0002`–`0004`** (RF-011): las cuentas existentes se conservan con los valores
  de relleno "Usuario sin nombre", 1900-01-01 y `ZZ`; si hay correos que solo difieren en
  mayúsculas, la migración se detiene y los nombra, sin fusionar ni borrar nada.

### Límites conocidos
- `bulk_create`, `update()` y SQL directo solo garantizan la unicidad del correo: no validan
  nombre, edad ni país ni dejan versión en el historial (criterio común de la spec).
- Un correo duplicado da `IntegrityError` (error de base de datos), no `ValidationError`: la
  futura API de registro deberá traducirlo a un mensaje legible.
- La exclusión de cuentas inactivas es por convención (D-07): el código que use `User.objects`
  las verá.
- El signup de allauth (`/auth/signup`) no pide nombre, fecha ni país, así que ya no puede
  crear usuarios (S-07). Lo resolverá la feature de registro.
- Si se borra físicamente a quien hizo un cambio, sus versiones quedan sin autor
  (`on_delete=SET_NULL`).
- Riesgo residual aceptado al cerrar: ningún test detectaría que el historial deje de registrar
  cambios de una instancia tras un guardado de `last_login` que falle.

## Cómo probarlo
Requisitos: Docker y la rama `feat/usuario-personalizado`.

1. Reconstruye la imagen (hay dependencias nuevas) y levanta la base de datos y Redis:
   `docker compose -f docker/docker-compose.yml build backend`
   `docker compose -f docker/docker-compose.yml up -d db redis`
2. Aplica las migraciones. Deberías ver `0002_user_profile_fields`, `0003_user_email_ci_unique`
   y `0004_historicaluser` en `OK`:
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py migrate`
3. Crea un superusuario sin preguntas; ahora exige los tres datos nuevos:
   `docker compose -f docker/docker-compose.yml run --rm -e DJANGO_SUPERUSER_PASSWORD=Prueba-123 backend python manage.py createsuperuser --noinput --email Admin@Example.com --name "Ana García" --birthdate 1990-05-10 --country es`
   Se guarda como `admin@example.com` y país `ES`. Si repites con `--email ADMIN@example.com`,
   falla con una traza de `IntegrityError` ("already exists"): es el choque de correo, ver
   "Límites conocidos". Con `--country XX` o `--birthdate 2020-01-01`, falla con el motivo en
   inglés.
4. Consulta el historial desde la consola de Django:
   `docker compose -f docker/docker-compose.yml run --rm backend python manage.py shell -c "from apps.accounts.models import User; print(list(User.history.values_list('email', 'history_type', 'history_user')))"`
   Verás `('admin@example.com', '+', None)`: alta hecha por consola, sin autor.
5. Ejecuta la suite completa (el mínimo de cobertura del 80 % se mide sobre todo el proyecto,
   así que ejecutar solo `apps/accounts` falla aunque pasen todos los tests):
   `docker compose -f docker/docker-compose.yml run --rm backend pytest -q`
   Deberías ver `124 passed` y una cobertura superior al 80 %.

## Marco teórico
### Borrado lógico (soft delete)
En vez de borrar la fila, se marca la cuenta como inactiva (`is_active = False`). Los datos
siguen ahí para auditoría o para reactivarla, y el correo sigue ocupado, así nadie puede
registrarse con él mientras tanto. El coste es que hay que acordarse de excluir las inactivas en
cada consulta de la aplicación: por eso existe `User.active`.

### Por qué no se filtra el gestor por defecto
Parece más seguro que `User.objects` oculte las inactivas, pero Django lo desaconseja. Las
comprobaciones de unicidad, el login, las exportaciones (`dumpdata`) y el panel de
administración usan el gestor por defecto. Si las inactivas desaparecieran de él, no se podrían
reactivar desde el admin y los choques de correo se detectarían tarde. Se eligió lo explícito
(`User.active`) a cambio de depender de una convención.

### Unicidad sin distinguir mayúsculas en la base de datos
`unique=True` compara textos exactos: "Ana@x.com" y "ana@x.com" serían dos correos distintos.
Normalizar en `save()` no basta, porque las cargas masivas y el SQL directo no pasan por
`save()`. La solución es un índice único sobre `LOWER(email)`: la base de datos compara ya en
minúsculas y rechaza el duplicado venga de donde venga.

### Valores de relleno en una migración
Al añadir un campo obligatorio a una tabla con filas, la base de datos necesita un valor para
las que ya existen. Se usa uno reconocible ("Usuario sin nombre", 1900-01-01, `ZZ`) que no pase
por dato real. `preserve_default=False` hace que ese valor solo se use al migrar y no quede como
valor por defecto de las cuentas nuevas.

### ISO 3166-1 alfa-2 y los códigos reservados
Es la lista oficial de códigos de país de dos letras (`ES`, `MX`, `AR`…). Algunos códigos
existen pero están reservados y no son países de la lista: `XK` (Kosovo, uso provisional) o
`ZZ` (desconocido). Por eso `ZZ` sirve como relleno: nunca se confunde con un país real.
`pycountry` mantiene la lista al día en lugar de copiarla a mano.

### Mensajes en inglés con `gettext_lazy`
El código devuelve sus errores en inglés y los marca para traducción. `gettext_lazy` no traduce
al importar el módulo, sino cuando el mensaje se muestra, en el idioma de esa petición. Así la
futura interfaz podrá mostrarlos en español sin tocar el código.

### Historial de cambios (auditoría)
Cada alta, cambio o borrado guarda una copia de la fila en una tabla paralela
(`accounts_historicaluser`) con la fecha, el tipo de cambio y quién lo hizo. La contraseña y la
fecha del último login se excluyen: la primera por seguridad, la segunda porque cambia en cada
inicio de sesión y llenaría el historial de versiones idénticas.

### Tests que prueban algo real: TDD y mutaciones
Un test que nunca ha fallado no demuestra nada. En TDD se escribe primero el test y se ve fallar,
y solo después se implementa. Cuando el código ya existía (migraciones, login de inactivas) se
usaron mutaciones: se estropea el código a propósito en una copia (por ejemplo, se cambia el
relleno), se comprueba que el test cae y se restaura. Así se descubrió, por ejemplo, que ningún
test protegía el guardado parcial, y se añadió uno.
