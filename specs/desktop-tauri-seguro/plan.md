# Plan: desktop-tauri-seguro
Estado: aprobado

## Módulos
### M-01 Política base de producción
Responsabilidad: `desktop/src-tauri/tauri.conf.json` declara en `app.security.csp` la política
base, como mapa de directivas: `default-src 'self'`, `script-src 'self'`, `style-src 'self'`,
`font-src 'self'`, `img-src 'self' data: blob:`, `connect-src 'self' ipc: http://ipc.localhost`,
`object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-src 'none'`,
`frame-ancestors 'none'`. Sin `'unsafe-inline'` ni `'unsafe-eval'`. Es la política que se aplica
cuando no hay backend definido. No se declara `devCsp`, porque en escritorio Tauri no lo aplica
(D-03).
RF: RF-001, RF-002, RF-003, RF-010

### M-02 Origen del backend
Responsabilidad: `desktop/src-tauri/src/backend_origin.rs` valida el valor de `VITE_API_BASE_URL`
que resuelve M-09 (esquema `http`/`https`, host y puerto opcional; se admite una ruta, pero no una
consulta ni un fragmento) y extrae su origen y el origen WebSocket equivalente (`ws`/`wss`).
`build.rs` incluye el archivo con `#[path]`, hace fallar la compilación si el valor es inválido y
exporta el origen a la app con `cargo:rustc-env=CONFIABILIDAD_BACKEND_ORIGIN=<origen>`, que es un
nombre interno y nadie lo define a mano. Un valor ausente o vacío significa «sin backend» y la
compilación sigue.
RF: RF-004, RF-010

### M-03 Aplicación de la política en arranque
Responsabilidad: `desktop/src-tauri/src/csp.rs` añade a `connect-src` los dos orígenes de M-02
cuando existen. `lib.rs` lo aplica sobre `Context::config_mut()` antes de arrancar, con el valor de
`option_env!("CONFIABILIDAD_BACKEND_ORIGIN")` que exporta `build.rs`. Tauri lee la
política de su configuración en tiempo de ejecución (`AppManager::csp`) y le suma los hashes de los
recursos.
RF: RF-004, RF-010

### M-04 Guardia de navegación y descargas
Responsabilidad: `desktop/src-tauri/src/navigation.rs` contiene un plugin interno (sin comandos ni
permisos) con dos ganchos:
- `on_navigation` permite solo el origen de la propia app (`tauri://localhost`,
  `http://tauri.localhost` en Windows y el origen del servidor de desarrollo en `cfg(dev)`) y las
  URL `blob:` creadas por ese origen. Cualquier otra navegación se ignora sin aviso.
- `on_download` acepta solo descargas `blob:`/`data:` de la propia app y las guarda en la carpeta
  de descargas del usuario.

La lógica de decisión son funciones puras, que se prueban sin ventana.
RF: RF-007, RF-011

### M-05 Cero permisos
Responsabilidad: se elimina `desktop/src-tauri/capabilities/default.json` (`core:default`) y no se
declara ninguna capability. Un test verifica que la configuración resultante no concede ningún
permiso.
RF: RF-005

### M-06 Política de desarrollo
Responsabilidad: `frontend/config/desktopDevCsp.ts` construye la política de M-01 + el origen de
`VITE_API_BASE_URL` tal como lo carga Vite en el modo de desarrollo (`loadEnv`) + `http://localhost:5173` y `ws://localhost:5173` + el nonce fijo en `script-src` y
`style-src`. `frontend/vite.config.ts` la envía como cabecera `Content-Security-Policy` del
servidor de desarrollo y activa `html.cspNonce`, solo cuando Vite sirve (`command === "serve"`) y
existe `TAURI_ENV_PLATFORM`, que la CLI de Tauri define para `beforeDevCommand`. El desarrollo web
fuera de Tauri y el build de producción no cambian.
RF: RF-006

### M-07 Compilación en los tres sistemas operativos
Responsabilidad: un workflow nuevo, `.github/workflows/desktop.yml`, que se dispara solo con
cambios en `desktop/**`, `frontend/**` o en el propio workflow. Tiene una matriz `ubuntu-latest`,
`windows-latest` y `macos-latest` y ejecuta `pnpm --filter desktop tauri build --debug --no-bundle`.
Sube el ejecutable de depuración como artefacto para la prueba manual de RF-009 y RF-011. En Linux
ejecuta además los tests de M-08 con `xvfb-run`.
RF: RF-008, RF-009 (artefacto para la prueba manual)

### M-08 Test de comportamiento
Responsabilidad: un test de integración Rust (`desktop/src-tauri/tests/policy_behavior.rs`) arranca
la app real, con las funciones públicas de M-03 y M-04, sobre una página de prueba
(`tests/fixtures/`) servida por el protocolo de Tauri. Esa página intenta cargar un script externo,
ejecutar uno en línea, insertar un estilo en línea, conectarse a un origen ajeno y navegar fuera. Al
terminar, codifica el resultado (eventos `securitypolicyviolation` y lo que llegó a ejecutarse) en
una navegación a un origen reservado (`https://report.invalid/…`). El gancho de M-04 la bloquea y el
test la lee.
RF: RF-002, RF-003, RF-004, RF-007, RF-010

### M-09 Lector de la configuración de la interfaz
Responsabilidad: `desktop/src-tauri/src/frontend_env.rs`, incluido por `build.rs`. Resuelve
`VITE_API_BASE_URL` con la prioridad de Vite en modo producción: entorno del proceso, después
`.env.production.local`, `.env.production`, `.env.local` y `.env`, todos de `frontend/`. Lee líneas
`CLAVE=valor`, con `export` opcional, comillas simples o dobles y comentarios de línea completa.
Rechaza, con un error que nombra el archivo y la línea, los valores con `$` (Vite los expande), los
valores multilínea y las comillas sin cerrar. Declara `cargo:rerun-if-changed` para cada uno de esos
archivos.
RF: RF-004, RF-010, RF-012

## Modelo de datos
No aplica: la feature no persiste datos.

## Decisiones
### D-01 Política base en `tauri.conf.json` y origen del backend añadido en arranque
Elegida: la política base fija en `tauri.conf.json` (M-01), y el origen del backend resuelto por `build.rs`
desde `VITE_API_BASE_URL` (M-09), exportado a la app y leído con `option_env!` y añadido a la configuración en tiempo de ejecución (M-03).
Descartada: generar `tauri.conf.json` o pasar `--config`/`TAURI_CONFIG` con un script por entorno.
Motivo: el JSON de fusión reemplaza listas enteras, así que habría que repetir toda la política en
cada entorno. Además, el script sería JS sin tipos dentro de `desktop/` (P-07). La función de Rust
se prueba con tests unitarios (P-04).

### D-02 Validación del origen en `build.rs`
Elegida: resolver y validar `VITE_API_BASE_URL` al compilar y fallar si es inválido, compartiendo el
archivo con la app mediante `#[path]`.
Descartada: validar en el arranque y cerrar la app.
Motivo: un error de configuración se ve en el CI o en la máquina de quien compila, nunca en la del
usuario final.

### D-03 Política de desarrollo servida por Vite
Elegida: cabecera CSP y `html.cspNonce` en el servidor de desarrollo de Vite, solo bajo Tauri (M-06).
Descartada: `app.security.devCsp` de Tauri.
Motivo: en escritorio, Tauri 2 carga `devUrl` sin proxy y no aplica ninguna política en desarrollo
(`PROXY_DEV_SERVER = cfg!(all(dev, mobile))`). `devCsp` no tendría efecto y RF-006 no se cumpliría.
Coste: la política vive en dos sitios (Rust y TS). La desviación se controla con tests en los dos
lados que comprueban la misma lista de directivas (ver Estrategia de tests).

### D-04 `ipc:` y `http://ipc.localhost` en `connect-src`
Elegida: incluirlos en la política base.
Descartada: `connect-src 'self'` a secas.
Motivo: es el canal interno de la propia app. Sin él, el puente de Tauri recurre a otro mecanismo y
registra violaciones en la consola, con lo que RF-009 fallaría. Con cero permisos (M-05), ese canal
no puede invocar ninguna función nativa.

### D-05 Guardia de navegación como plugin interno
Elegida: un plugin interno con `on_navigation` y `on_download` (M-04), que mantiene la ventana
declarada en `tauri.conf.json`.
Descartada: crear la ventana en código con `WebviewWindowBuilder`.
Motivo: el plugin se aplica a todo webview, también a los que se creen en el futuro, y no cambia
cómo se declara la ventana.

### D-06 Cero permisos eliminando la capability
Elegida: eliminar `capabilities/default.json`.
Descartada: dejar una capability con `"permissions": []`.
Motivo: un archivo vacío invita a volver a llenarlo sin justificación. Su ausencia, junto con un
test que lo comprueba, hace visible cualquier permiso que se añada.

### D-07 Test de comportamiento propio con WebKitGTK y `xvfb-run`
Elegida: un test de integración Rust sobre la app real en Linux, que informa de los resultados
mediante una navegación bloqueada (M-08). No añade dependencias al proyecto, pero el CI instala el
paquete de sistema `xvfb`.
Descartada: `tauri-driver` + WebdriverIO.
Motivo: añadiría dependencias de Rust y npm y no funciona en macOS. Playwright también queda
descartado, porque prueba Chromium y no el webview de Tauri.
Coste: el test de comportamiento solo corre en Linux (WebKitGTK). En Windows (WebView2) y macOS
(WKWebView), el comportamiento se cubre con la prueba manual de RF-009 y con los tests de
configuración, que son los mismos en los tres sistemas.

### D-08 Workflow propio con filtro de rutas
Elegida: `.github/workflows/desktop.yml` con `on.*.paths`.
Descartada: añadir la matriz al job `desktop` de `ci.yml` o usar una acción de filtrado de rutas.
Motivo: `ci.yml` no tiene filtro de rutas (RF-008 pide compilar solo si cambian `desktop/` o
`frontend/`), y una acción de terceros sería una dependencia nueva. El job `desktop` de `ci.yml`
(rustfmt y clippy) se mantiene.
Riesgo: si alguna vez este workflow se marca como check obligatorio, los PR que no lo disparan se
quedan esperando.

### D-09 Nonce fijo
Elegida: el valor literal `confiabilidad-dev`, definido solo en M-06.
Descartada: un nonce aleatorio por arranque.
Motivo: lo decidiste en C-08 (nonce fijo o de un solo uso). El test de M-01 comprueba que la
política de producción no contiene ningún `'nonce-…'` (C-09, verificación solo sobre la política).

### D-10 Resolución propia con rechazo de lo ambiguo
Elegida: un lector mínimo propio que rechaza todo lo que Vite podría interpretar de otra forma, como
la expansión, el multilínea y las comillas sin cerrar.
Descartada: preguntarle a Vite el valor, ejecutando Node desde `build.rs`.
Motivo: `build.rs` dependería de Node y de `node_modules` en cada `cargo build`, incluido
`cargo clippy`. Además, no hay que añadir dependencias de Rust (un crate `dotenvy`, que tampoco
expande igual que `dotenv-expand`).
Coste: si alguien usa una sintaxis de `.env` válida para Vite pero rechazada por el lector, la
compilación falla, aunque nunca acepta un valor distinto. Si el frontend se compila por separado
con otra configuración y se empaqueta ese `dist`, no se detecta (riesgo aceptado en `sdd-cambio`).

### D-11 `desktop/` lee los `.env*` de `frontend/`
Elegida: `build.rs` lee esos archivos como datos de configuración.
Descartada: exigir que el backend se defina solo en el entorno (C-11).
Motivo: lo decidiste en C-11. No se comparte código entre carpetas: es lectura de configuración y
no contradice P-08, que prohíbe compartir código y duplicar React.

## Estrategia de tests
- **Unitarios en Rust** (`cargo test`, los tres sistemas):
  - `backend_origin`: aceptados, rechazados, derivación `ws`/`wss` y ausencia.
  - `csp`: política sin backend igual a la base y con backend solo con los dos orígenes añadidos.
  - `navigation`: orígenes permitidos y bloqueados, `blob:` propio y ajeno, descargas aceptadas y
    rechazadas.
  - Configuración: se lee `tauri.conf.json` y se comprueba cada directiva de M-01, la ausencia de
    `'unsafe-inline'`, `'unsafe-eval'` y `'nonce-…'`, la ausencia de `devCsp` y que no hay
    capabilities ni permisos.
  - `backend_origin` además: admite una ruta (`https://api.example.com/base`) y extrae el origen;
    rechaza una consulta o un fragmento.
  - `frontend_env`: la prioridad entre el entorno y los cuatro archivos; las comillas, `export` y
    comentarios; el rechazo de `$`, del multilínea y de las comillas sin cerrar, con el nombre del
    archivo y la línea; y la ausencia del valor en todas las fuentes. Cubre RF-010 y RF-012.
  Cubren RF-001 a RF-005, RF-007, RF-010 y RF-011 (lógica).
- **Unitarios en TS** (Vitest): `desktopDevCsp` produce la base + el origen del servidor de
  desarrollo + el nonce, con y sin backend, y Vite solo la activa bajo `serve` con
  `TAURI_ENV_PLATFORM`. Cubren RF-006. La lista de directivas base se compara en los dos lados
  con el mismo valor literal (D-03).
- **Integración en Rust sobre webview real** (Linux en CI, `xvfb-run`): M-08. Cubre RF-002,
  RF-003, RF-004, RF-007 y RF-010 con comportamiento observable.
- **CI**: la matriz de M-07 cubre RF-008.
- **Manual** (`HUMAN_TODO.md`): con el artefacto de depuración de M-07, en los tres sistemas, se
  revisa que la consola no tiene violaciones y que se puede guardar un archivo generado. Cubre RF-009
  y RF-011. En `tauri dev` se comprueba que React Refresh y los estilos funcionan (RF-006).
- **Mutación** (por tarea, según el flujo): sobre las funciones puras de M-02, M-03, M-04 y M-06.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01 | Unitario Rust (configuración) |
| RF-002 | M-01, M-08 | Unitario Rust (configuración) + integración webview |
| RF-003 | M-01, M-08 | Unitario Rust (configuración) + integración webview |
| RF-004 | M-02, M-03, M-08, M-09 | Unitario Rust + integración webview |
| RF-005 | M-05 | Unitario Rust (configuración) |
| RF-006 | M-06 | Unitario TS + manual en `tauri dev` |
| RF-007 | M-04, M-08 | Unitario Rust + integración webview |
| RF-008 | M-07 | CI (matriz de 3 sistemas) |
| RF-009 | M-07 | Manual con el artefacto de depuración (3 sistemas) |
| RF-010 | M-01, M-02, M-03, M-08, M-09 | Unitario Rust + integración webview |
| RF-011 | M-04 | Unitario Rust + manual (3 sistemas) |
| RF-012 | M-09 | Unitario Rust + comprobación con `cargo build` que falla con un `.env` que usa `$` |

## RF sin cobertura
Ninguno.
