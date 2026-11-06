# Tareas: desktop-tauri-seguro
Estado: aprobado

Rutas relativas a `desktop/src-tauri/` salvo que se indique. "Suite verde desktop" =
`pnpm --filter frontend build` (genera `frontend/dist`, que necesita `generate_context!`) +
`cargo test --manifest-path desktop/src-tauri/Cargo.toml` +
`cargo fmt --check --manifest-path desktop/src-tauri/Cargo.toml` +
`cargo clippy --manifest-path desktop/src-tauri/Cargo.toml --all-targets -- -D warnings`.
"Suite verde frontend" = `pnpm --filter frontend test` + `pnpm --filter frontend typecheck` +
`pnpm --filter frontend lint`. En cada tarea, antes de marcarla, se prueba al menos un mutante del
código que introduce y debe hacer fallar sus tests.

- [x] T-001 Política base estricta en `tauri.conf.json`
  RF: RF-001, RF-002, RF-003, RF-010 | Depende de: — | Archivos: 2
  Archivos: `tauri.conf.json`, `tests/config_policy.rs`.
  Hecho cuando: `tests/config_policy.rs` lee `tauri.conf.json` y comprueba que `app.security.csp`
  es un mapa con exactamente las directivas de M-01 (política base de producción); que ninguna
  contiene `'unsafe-inline'`, `'unsafe-eval'`, `'nonce-` ni `*`; que no existe `devCsp`; y que
  `connect-src` no contiene orígenes fuera de `'self' ipc: http://ipc.localhost`. El test falla con
  el `"csp": null` actual y pasa tras el cambio. Suite verde desktop.
  Decisiones: el test compara las directivas como conjuntos de fuentes y acepta en el JSON tanto
  una cadena separada por espacios como una lista, porque Tauri admite las dos formas — [Cierto] —
  revertir: comparar el valor literal del JSON. El test de `devCsp` pasa desde el principio porque
  hoy no existe; se mantiene como guarda de regresión — [Cierto] — revertir: borrar el test.

- [x] T-002 Cero permisos nativos
  RF: RF-005 | Depende de: T-001 | Archivos: 2
  Archivos: `capabilities/default.json` (se elimina), `tests/config_policy.rs`.
  Hecho cuando: un test comprueba que `capabilities/` no existe o no contiene archivos, y que
  `tauri.conf.json` no declara `app.security.capabilities` con contenido. El test falla con
  `core:default` y pasa tras eliminar el archivo. `cargo build` sigue compilando. Suite verde
  desktop.
  Decisiones: además del test, se comprobó que el ACL que resuelve Tauri
  (`gen/schemas/capabilities.json`) queda en `{}`; no se versiona porque `gen/schemas` está en
  `.gitignore` — [Cierto] — revertir: no aplica.

- [ ] T-003 Validación del origen del backend
  RF: RF-004, RF-010 | Depende de: — | Archivos: 2
  Archivos: `src/backend_origin.rs`, `src/lib.rs` (solo la declaración del módulo).
  Hecho cuando: hay tests unitarios en `backend_origin.rs` que cumplen todo esto:
  - `parse` acepta `http://localhost:8000`, `https://api.example.com` y
    `https://api.example.com/base/`, extrae el origen (`https://api.example.com`) y deriva
    `ws://localhost:8000` y `wss://api.example.com`;
  - rechaza, con un error distinto para cada caso, un esquema distinto de `http`/`https`, un valor
    sin host y uno con consulta o fragmento;
  - una variable ausente o vacía devuelve «sin backend».

  Suite verde desktop.

- [ ] T-013 Lector de la configuración de la interfaz
  RF: RF-010, RF-012 | Depende de: — | Archivos: 2
  Archivos: `src/frontend_env.rs`, `src/lib.rs` (solo `#[cfg(test)] mod frontend_env;`, porque el
  módulo lo usa `build.rs`).
  Hecho cuando: hay tests unitarios que cumplen todo esto:
  - con un directorio temporal, la resolución de `VITE_API_BASE_URL` respeta la prioridad entorno >
    `.env.production.local` > `.env.production` > `.env.local` > `.env`;
  - interpreta `export`, las comillas simples y dobles y los comentarios de línea completa;
  - rechaza un valor con `$`, uno multilínea y uno con comillas sin cerrar, con un error que nombra
    el archivo y la línea;
  - sin valor en ninguna fuente, devuelve «sin backend»;
  - lista los archivos que hay que vigilar para `rerun-if-changed`.

  Suite verde desktop.

- [ ] T-004 La compilación resuelve, valida y exporta el origen del backend
  RF: RF-004, RF-010, RF-012 | Depende de: T-003, T-013 | Archivos: 1
  Archivos: `build.rs`.
  Hecho cuando: `build.rs` incluye `src/frontend_env.rs` y `src/backend_origin.rs` con `#[path]`;
  declara `rerun-if-env-changed=VITE_API_BASE_URL` y `rerun-if-changed` para cada archivo de T-013;
  aborta con el mensaje del error si la resolución o la validación fallan; y si hay backend, emite
  `cargo:rustc-env=CONFIABILIDAD_BACKEND_ORIGIN=<origen>`. Se comprueba con cuatro ejecuciones de
  `cargo build`:
  - con `VITE_API_BASE_URL=ftp://example.com` en el entorno, falla y muestra el error;
  - con un `frontend/.env.production.local` temporal que contiene `VITE_API_BASE_URL=$HOST`, falla
    y nombra el archivo y la línea;
  - sin la variable en ninguna fuente, compila;
  - con `VITE_API_BASE_URL=https://api.example.com/base` en el entorno, compila.

  Suite verde desktop.

- [ ] T-005 El origen del backend se añade a `connect-src` en el arranque
  RF: RF-004, RF-010 | Depende de: T-001, T-004 | Archivos: 2
  Archivos: `src/csp.rs`, `src/lib.rs`.
  Hecho cuando: hay tests unitarios en `csp.rs` que cumplen todo esto:
  - sin backend, la política devuelta es idéntica a la de `tauri.conf.json`;
  - con `https://api.example.com`, `connect-src` añade exactamente `https://api.example.com` y
    `wss://api.example.com`, y ninguna otra directiva cambia.

  `run()` aplica la función sobre `Context::config_mut()` con el valor de
  `option_env!("CONFIABILIDAD_BACKEND_ORIGIN")`, que exporta `build.rs` (T-004), y expone una función pública que configura un
  `Builder` y un `Context` dados, para reutilizarla en T-011. Suite verde desktop.

- [ ] T-006 Decisión de navegación y descarga
  RF: RF-007, RF-011 | Depende de: — | Archivos: 2
  Archivos: `src/navigation.rs`, `src/lib.rs` (solo la declaración del módulo).
  Hecho cuando: hay tests unitarios de dos funciones puras que cumplen todo esto:
  - `allows_navigation` acepta `tauri://localhost/…`, `http://tauri.localhost/…`,
    `blob:tauri://localhost/<uuid>` y, solo con `cfg(dev)`, `http://localhost:5173/…`;
  - `allows_navigation` rechaza `https://example.com`, el origen del backend,
    `blob:https://example.com/<uuid>`, `http://localhost:5173` fuera de `cfg(dev)` y
    `http://tauri.localhost.example.com`;
  - `allows_download` acepta `blob:` y `data:` de la propia app y rechaza cualquier URL `http(s)`.

  Suite verde desktop.

- [ ] T-007 Plugin interno de navegación y descargas
  RF: RF-007, RF-011 | Depende de: T-005, T-006 | Archivos: 2
  Archivos: `src/navigation.rs`, `src/lib.rs`.
  Hecho cuando: un plugin interno sin comandos registra `on_navigation` (que devuelve
  `allows_navigation`) y `on_download`. `on_download` acepta solo lo que permite
  `allows_download`, fija el destino en la carpeta de descargas del usuario (con el nombre sugerido)
  y rechaza el resto. La función pública de T-005 lo registra. Hay un test unitario que comprueba
  que la ruta de destino queda dentro de la carpeta de descargas y que un nombre con `../` no sale
  de ella. Suite verde desktop.

- [ ] T-008 Política de desarrollo para Tauri
  RF: RF-006 | Depende de: T-001 | Archivos: 3
  Archivos: `frontend/config/desktopDevCsp.ts`, `frontend/config/desktopDevCsp.test.ts`,
  `frontend/tsconfig.json` (incluye `config` para que pase `typecheck`).
  Hecho cuando: los tests de Vitest cumplen todo esto:
  - `desktopDevCsp()` devuelve las directivas de M-01 (política base de producción), con el mismo
    literal que el test de T-001, más `http://localhost:5173` y `ws://localhost:5173` en
    `connect-src` y `'nonce-confiabilidad-dev'` en `script-src` y `style-src`;
  - recibe el valor de `VITE_API_BASE_URL`; con `https://api.example.com/base`, añade además
    `https://api.example.com` y `wss://api.example.com` a `connect-src`; sin valor, no añade nada;
  - ninguna directiva contiene `'unsafe-inline'` ni `'unsafe-eval'`.

  Suite verde frontend.

- [ ] T-009 Vite envía la política solo bajo Tauri
  RF: RF-006 | Depende de: T-008 | Archivos: 3
  Archivos: `frontend/vite.config.ts`, `frontend/config/desktopDevCsp.ts`,
  `frontend/config/desktopDevCsp.test.ts`.
  Hecho cuando: los tests de Vitest de una función `devServerSecurity(command, env)` cumplen todo
  esto:
  - con `serve` y `TAURI_ENV_PLATFORM` definido, devuelve la cabecera `Content-Security-Policy` y
    `html.cspNonce = "confiabilidad-dev"`;
  - sin `TAURI_ENV_PLATFORM`, o con `build`, no devuelve nada.

  `vite.config.ts` usa esa función y le pasa el `VITE_API_BASE_URL` de `loadEnv(mode, ".")`, la misma
  llamada que ya usa el proxy. `pnpm --filter frontend build` produce un `dist/index.html`
  sin atributos `nonce`. Suite verde frontend.

- [ ] T-010 Compilación del ejecutable en los tres sistemas
  RF: RF-008, RF-009 | Depende de: T-007, T-009 | Archivos: 1
  Archivos: `.github/workflows/desktop.yml`.
  Hecho cuando: el workflow se dispara en `push` y `pull_request` solo con cambios en
  `desktop/**`, `frontend/**` o en el propio archivo. Su matriz `ubuntu-latest`, `windows-latest` y
  `macos-latest` ejecuta `pnpm --filter desktop tauri build --debug --no-bundle` y
  `cargo test --manifest-path desktop/src-tauri/Cargo.toml`, y sube el ejecutable de depuración
  como artefacto. La ejecución del PR de la entrega aparece en verde en los tres sistemas, y un
  commit de prueba que rompe la compilación (revertido después) la pone en rojo.

- [ ] T-011 Test de comportamiento de la política sobre el webview real
  RF: RF-002, RF-003, RF-004, RF-007, RF-010 | Depende de: T-007 | Archivos: 3
  Archivos: `tests/policy_behavior.rs`, `tests/fixtures/index.html`, `tests/fixtures/tauri.conf.json`.
  Hecho cuando: el test arranca la app con la función pública de T-005 y la configuración de
  prueba, y la página de prueba informa mediante una navegación bloqueada a
  `https://report.invalid/…`. Con `xvfb-run cargo test --test policy_behavior` en Linux, el test
  comprueba todo esto:
  - el script externo no se ejecutó;
  - el script en línea no se ejecutó;
  - el estilo en línea no se aplicó;
  - la conexión a `https://example.com` se bloqueó;
  - la navegación a `https://example.com` no cambió la página.

  El test fuera de Linux se marca `#[cfg(target_os = "linux")]`. La primera acción de la tarea es
  comprobar que `generate_context!` acepta la configuración de prueba desde un test de integración.
  Si no lo acepta, se detiene y se informa (desviación del plan).

- [ ] T-012 Test de comportamiento en CI
  RF: RF-002, RF-003, RF-004, RF-007, RF-010 | Depende de: T-010, T-011 | Archivos: 1
  Archivos: `.github/workflows/desktop.yml`.
  Hecho cuando: el job de Linux instala `xvfb` y ejecuta los tests con `xvfb-run`; la ejecución del
  PR de la entrega muestra `policy_behavior` en verde, y un mutante en `allows_navigation` (aceptar
  cualquier origen) la pone en rojo.

## Entregas
Rama de integración: feat/desktop-tauri-seguro (los PR de las entregas van contra ella; ver `AGENTS.md`)

- E-01 La app de escritorio arranca con la CSP estricta y sin permisos
  Tareas: T-001, T-002 | Líneas estimadas: 120 | Rama: feat/desktop-tauri-seguro-csp-produccion
  Cómo probarlo: `cargo test`; `pnpm --filter desktop tauri build --debug --no-bundle`; abrir el
  ejecutable y comprobar en las herramientas de desarrollo la cabecera CSP y que la consola no
  muestra violaciones.

- E-02 La política admite solo el backend configurado para la interfaz
  Tareas: T-013, T-003, T-004, T-005 | Líneas estimadas: 380 | Rama: feat/desktop-tauri-seguro-origen-backend
  Cómo probarlo: `cargo test`; las cuatro compilaciones de T-004; con
  `VITE_API_BASE_URL=http://localhost:8000`, compilar la versión de depuración y comprobar que el
  registro llega al backend y que `fetch("https://example.com")` en la consola se bloquea.

- E-03 La ventana no navega fuera de la app y guarda los archivos generados
  Tareas: T-006, T-007 | Líneas estimadas: 200 | Rama: feat/desktop-tauri-seguro-navegacion
  Cómo probarlo: `cargo test`; en el ejecutable de depuración, ejecutar en la consola
  `location.href = "https://example.com"` (la app no cambia) y descargar un `Blob` con un enlace
  `download` (el archivo aparece en la carpeta de descargas).

- E-04 `tauri dev` aplica la misma política con el nonce del servidor de desarrollo
  Tareas: T-008, T-009 | Líneas estimadas: 150 | Rama: feat/desktop-tauri-seguro-csp-desarrollo
  Cómo probarlo: `pnpm --filter frontend test`; `pnpm --filter desktop tauri dev`, editar un
  componente (React Refresh lo recarga y los estilos se ven); en la consola, insertar un `<script>`
  en línea sin nonce (se bloquea); `pnpm --filter frontend dev` en el navegador sigue sin política.

- E-05 Compilación en los tres sistemas y prueba de comportamiento en CI
  Tareas: T-010, T-011, T-012 | Líneas estimadas: 300 | Rama: feat/desktop-tauri-seguro-ci-tres-sistemas
  Cómo probarlo: abrir el PR y ver el workflow `desktop` en verde en los tres sistemas; descargar el
  artefacto de cada sistema y seguir el `HUMAN_TODO.md` de la feature (RF-009 y RF-011).

## RF sin tarea
Ninguno.
