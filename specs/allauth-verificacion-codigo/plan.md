# Plan: allauth-verificacion-codigo
Estado: aprobado

Tipo: spike. Todo el código vive en tests (S-08); no hay código de producción.
Versión de allauth en la exploración: 65.19.4 (S-02).
`D-01` queda reservada para la decisión final del spike (RF-006), que se escribe en `resumen.md`;
las decisiones de este plan empiezan en `D-02`.

## Contexto técnico (lectura previa del código de allauth 65.19.4)
- El estado de la verificación por código se guarda en la sesión (clave
  `account_email_verification_code`) y se borra al completar la verificación. Es un indicio para
  RF-003/RF-004, no una respuesta: la dan los tests.
- Reenviar el código genera uno nuevo y sustituye al anterior en la sesión (RF-008).
- Las rutas `auth/code/request` y `auth/code/resend` solo se registran si
  `ACCOUNT_LOGIN_BY_CODE_ENABLED` está activo al importar las URLs. Signup, verify y resend existen
  siempre.
- El adapter expone `stash_verified_email` / `is_email_verified`, `new_user`, `save_user`,
  `set_password` y `confirm_email`, candidatos para RF-005 y RF-007.

## Módulos
Todos en `backend/apps/accounts/tests/spike_allauth/`.

### M-01 Configuración del spike (`conftest.py`)
Responsabilidad: fixture que activa, solo durante cada test, la verificación obligatoria por
código y la protección antienumeración (explícita, `ACCOUNT_PREVENT_ENUMERATION`, para no
depender del valor por defecto de allauth), y desactiva solo el límite de signups por IP, que la
propia suite agota. El reenvío y el login por código se activan en los tests o fixtures que los
necesitan. Incluye:
- un cliente headless parametrizado (`browser` / `app`), que abstrae cómo se mantiene la sesión
  (cookie o `X-Session-Token`) y cómo se abre una "sesión nueva";
- una utilidad que extrae el último código del buzón de correo de test.
RF: RF-001…RF-005, RF-008

### M-02 Recarga de las URLs de allauth (en `conftest.py`)
Responsabilidad: tras cambiar los settings, recargar `allauth.headless.urls` y el urlconf raíz
(`ROOT_URLCONF`) y limpiar la caché de URLs, para que existan las rutas que dependen de settings
(login por código). Al terminar el test se vuelven a recargar, para que desaparezcan. No hay un
`urls.py` propio del spike (sería un envoltorio sin función). Excepción de imports: RF-007.
RF: RF-002

### M-03 Casos de Q1 (`test_q1_user_existence.py`)
Responsabilidad:
- signup con verificación obligatoria: ¿existe fila de usuario antes de validar el código?
  (RF-001);
- código para un correo desconocido: ¿llega un código real al buzón y validarlo crea el usuario?
  (RF-002).
RF: RF-001, RF-002

### M-04 Casos de Q2 (`test_q2_code_reuse.py`)
Responsabilidad:
- segunda validación en la misma sesión (RF-003);
- validación desde otra sesión, antes y después de una primera validación (RF-004);
- reenvío: ¿se rechaza el código anterior y se emite uno nuevo? (RF-008).
RF: RF-003, RF-004, RF-008

### M-05 Entrada tardía (`test_late_entry.py`)
Responsabilidad: simular un registro pendiente con el código confirmado; al fijar la contraseña,
convertirlo en usuario a través de allauth (adapter y gestor de `EmailAddress`) con el correo
verificado; comprobar el login y la consulta de sesión en ambos clientes.
RF: RF-005

### M-06 Adapter experimental (`adapters.py`)
Responsabilidad: subclase de `DefaultAccountAdapter`, usada solo en tests mediante
`ACCOUNT_ADAPTER`, con las variantes "config + adapter" de RF-007. Variantes previstas:
- Q1: `save_user` sin persistir; `stash_verified_email` / `is_email_verified`.
- Q2: revisar si algún método público controla la invalidación del código; si no lo hay, se
  deja constancia.
RF: RF-007 (y RF-001…RF-004 en sus variantes)

### M-07 Informe (`specs/allauth-verificacion-codigo/resumen.md`)
Responsabilidad: tabla Q1/Q2 por cliente con la evidencia (nombre del test), la versión probada,
la lista de variantes intentadas para cada "no", la decisión D-01, un marco teórico (código ligado
a la sesión, replay, "consumir al completar") y cómo reproducirlo.
RF: RF-006, RF-007

## Modelo de datos
Sin modelos nuevos ni migraciones. Se usan `accounts.User` y el modelo `EmailAddress` de allauth
(con su gestor). El registro pendiente se simula en memoria dentro del test (D-08).

## Decisiones

### D-02 Ubicación del código del spike
Elegida: paquete de tests `apps/accounts/tests/spike_allauth/`.
Descartada: una app nueva (`apps/spike`).
Motivo: una app exige `INSTALLED_APPS` y deja huella en producción (S-08).

### D-03 Configuración de verificación
Elegida: override de settings por test (fixture `settings` de pytest-django), que se restaura al
terminar.
Descartada: un módulo `config/settings_spike.py` con su propio `DJANGO_SETTINGS_MODULE`.
Motivo: el módulo aparte no correría en la misma ejecución del CI y duplicaría configuración; el
override deja `auth-headless` intacto (S-06).

### D-04 Rutas condicionadas
Elegida: recargar `allauth.headless.urls` y el urlconf raíz tras el override, y otra vez al
terminar.
Descartada: activar `ACCOUNT_LOGIN_BY_CODE_ENABLED` globalmente.
Motivo: las rutas se fijan al importar y el urlconf raíz guarda en caché las incluidas;
activarlo globalmente cambiaría `auth-headless`. Recargar solo el módulo de allauth no basta si
otro test ya resolvió URLs (se comprobó en T-002).

### D-05 Obtención del código
Elegida: extraerlo del correo en el buzón de test (`mail.outbox`).
Descartada: leer la clave de sesión donde allauth lo guarda.
Motivo: la clave de sesión es interna (RF-007) y el usuario real solo tiene el correo.

### D-06 Cobertura de ambos clientes
Elegida: cada caso se parametriza por cliente (`browser` / `app`). "Otra sesión" significa un
cliente nuevo sin cookies (browser) o sin token o con otro token (app).
Descartada: tests duplicados por cliente.
Motivo: una sola definición por caso; si los clientes divergen, se ve en el id del parámetro
(regla de RF-006).

### D-07 Tipo de aserción
Elegida: aserciones estrictas sobre lo observado; la hipótesis se escribe antes de ejecutar y se
corrige con lo observado (S-07).
Descartada: `xfail` para los "no".
Motivo: `xfail` oculta los cambios de comportamiento; las aserciones estrictas hacen que el CI
avise si una versión nueva los altera (S-05).

### D-08 Simulación del registro pendiente
Elegida: un objeto en memoria dentro del test (email, datos, código confirmado).
Descartada: un modelo Django de test.
Motivo: un modelo exige app y migración (S-08); lo que se prueba es la conversión, no el
almacenamiento (S-10).

### D-09 Conversión a usuario
Elegida: a través de allauth: `adapter.new_user` + `adapter.set_password` + alta del correo con
el gestor de `EmailAddress` + `adapter.confirm_email` para marcarlo como verificado.
Descartada: crear `EmailAddress(verified=True)` escribiendo directamente con el ORM.
Motivo: C-11 exige pasar por allauth; así se comprueba que la vía oficial deja al usuario en un
estado que su login acepta.

### D-10 Registro de la versión
Elegida: la versión probada se anota en `resumen.md`.
Descartada: un test que fije la versión.
Motivo: rompería con cada actualización aunque el comportamiento no cambie; los tests de
caracterización ya detectan los cambios que importan.

## Estrategia de tests
- **Integración (API headless con el `Client` de Django)**: M-03, M-04 y M-05, parametrizados por
  cliente → RF-001…RF-005, RF-008. Las variantes de M-06 se ejecutan como casos adicionales →
  RF-007.
- **Tipo**: caracterización (S-05, S-07); sin código de producción, así que P-05 no cambia
  (`*/tests/*` está excluido de cobertura). La suite completa, incluida `auth-headless`, debe
  seguir en verde (CF-4).
- **Tipos y estilo**: los tests pasan `mypy` estricto, `ruff` y `black` (P-06, P-07).
- **Ejecución**: con Postgres, como el CI (`DATABASE_URL`); en esta sesión remota, contra la base
  de datos disponible en el entorno.
- **Revisión RF-007**: grep de los imports de allauth en `spike_allauth/`; solo se permiten
  `allauth.account.adapter`, `allauth.account.models` y settings, más la excepción de
  `allauth.headless.urls`. El grep incluye los imports por texto:
  `grep -rnE 'from allauth|import allauth|import_module\("allauth' spike_allauth/`.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-03, M-06 | integración (browser + app) |
| RF-002 | M-01, M-02, M-03 | integración (browser + app) |
| RF-003 | M-01, M-04, M-06 | integración (browser + app) |
| RF-004 | M-01, M-04, M-06 | integración (browser + app) |
| RF-005 | M-01, M-05 | integración (browser + app) |
| RF-006 | M-07 | documento (revisión) |
| RF-007 | M-06, M-07 | integración (variantes) + revisión de imports |
| RF-008 | M-01, M-04 | integración (browser + app) |

## RF sin cobertura
Ninguno.
