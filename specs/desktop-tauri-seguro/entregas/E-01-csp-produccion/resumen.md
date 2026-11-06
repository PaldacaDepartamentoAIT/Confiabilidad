# Entrega E-01 · La app de escritorio arranca con la CSP estricta y sin permisos

Rama: `feat/desktop-tauri-seguro-csp-produccion` · PR: pendiente ·
Líneas de código y tests: 125 (límite: 400).

## Qué se hizo
- `desktop/src-tauri/tauri.conf.json` declara una política de seguridad de contenido (CSP)
  estricta. Scripts, estilos y fuentes solo pueden venir de la propia app. Las imágenes pueden venir
  de la app o generarse en memoria (`data:`, `blob:`). Las conexiones solo se permiten con la app y
  con su canal interno (`ipc:`). No se permiten objetos incrustados, marcos ni formularios hacia
  otros orígenes. No hay `'unsafe-inline'`, `'unsafe-eval'` ni comodines.
- Se eliminó la capability `core:default`. La interfaz no tiene ningún permiso nativo: el ACL que
  resuelve Tauri al compilar está vacío.
- Un test lee la configuración y falla si la política cambia, si aparece una fuente permisiva, si
  se declara una política distinta para desarrollo (`devCsp`) o si se añade cualquier capability.
- Se comprobó en Linux (WebKitGTK, bajo `xvfb`) que el ejecutable de depuración arranca y muestra
  la interfaz completa, con estilos y fuentes.
- Todavía no se permite ningún backend: lo añade E-02. Por eso, desde esta entrega, la app de
  escritorio no puede llamar a la API.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Política base estricta en `tauri.conf.json` | `709d40b` |
| T-002 | Cero permisos nativos | `38dc5c6` |

## Cómo ejecutarlo y probarlo
En Linux hacen falta las bibliotecas de sistema de Tauri. En Windows y macOS no hace falta este
paso.
```bash
sudo apt-get install -y libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev patchelf
```

Desde la raíz del repositorio, instala las dependencias y compila el frontend:
```bash
pnpm install
```

```bash
pnpm --filter frontend build
```

Ejecuta los tests del desktop:
```bash
cargo test --manifest-path desktop/src-tauri/Cargo.toml
```
Deberías ver `config_policy` con 5 tests en verde.

Compila el ejecutable de depuración, que usa la política de producción:
```bash
pnpm --filter desktop tauri build --debug --no-bundle
```
Deberías ver la ruta del ejecutable en `desktop/src-tauri/target/debug/`.

Ábrelo:
```bash
./desktop/src-tauri/target/debug/confiabilidad-desktop
```
Deberías ver la ventana con la interfaz completa. En Windows, el ejecutable es
`desktop\src-tauri\target\debug\confiabilidad-desktop.exe`, y en macOS, el de la misma ruta sin
extensión.

Abre las herramientas de desarrollo: clic derecho → **Inspeccionar elemento**. Si la consola
muestra algún error de *Content Security Policy*, la entrega falla. Después, escribe en la consola:
```js
fetch("https://example.com")
```
Deberías ver un error de *Content Security Policy* que bloquea la conexión.

En la misma consola:
```js
const s = document.createElement("script"); s.src = "https://example.com/x.js"; document.head.append(s)
```
Deberías ver un error de *Content Security Policy* que bloquea el script.

## Marco teórico
- **CSP (Content Security Policy).** Es una lista, enviada con la página, que dice al navegador (aquí,
  el webview de la app) de dónde puede cargar cada tipo de recurso. Si alguien consigue inyectar un
  `<script>` en la página, el navegador se niega a ejecutarlo porque no viene de un origen
  permitido. Es la segunda barrera: la primera es no tener inyecciones.
- **Capabilities y permisos de Tauri.** El código JavaScript de la ventana solo puede usar funciones
  nativas (archivos, ventanas, notificaciones…) si una capability se lo concede. `core:default`
  concedía varios grupos que la interfaz no usa. Sin capabilities, un script inyectado que superara
  la CSP tampoco podría tocar el sistema.
