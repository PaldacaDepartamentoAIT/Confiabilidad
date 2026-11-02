# Entrega E-08 · Identidad visual, proxy y enrutador

Rama: `feat/registro-flujo-identidad-visual` · PR: pendiente ·
Líneas de código y tests: 341 (límite: 400).

## Qué se hizo
- **Paleta Niebla marina** (`frontend/src/styles/tokens.css`): los colores de los dos temas de
  `docs/identidad-visual.md` como variables CSS (`--color-canvas`, `--color-action`…). El tema
  oscuro se aplica solo cuando el sistema operativo lo pide (`prefers-color-scheme`); todavía no
  hay botón para cambiarlo (D-13). Un test lee el CSS y comprueba cada color de las dos tablas.
- **Estilos base** (`frontend/src/styles/base.css`): lienzo plano y bloques opacos, botones en
  píldora con el color de acción, casillas y campos con borde de línea fuerte, foco visible de 3 px
  separado 2 px, el código de verificación en JetBrains Mono y sin animaciones si el sistema pide
  reducir el movimiento.
- **Fuentes** `@fontsource-variable/manrope` y `@fontsource-variable/jetbrains-mono` (dependencias
  nuevas aprobadas el 2026-10-30), cargadas en `main.tsx`; funcionan sin conexión en el escritorio.
- **Proxy de desarrollo**: Vite reenvía `/api` al backend (`VITE_BACKEND_URL`; en Docker,
  `http://backend:8000`), para que la web hable con la API en su mismo origen.
- **Enrutador mínimo** (`frontend/src/routing/router.ts`), sin dependencias: lee la ruta y el
  fragmento, navega sin recargar y sigue el botón «atrás». La aplicación pasa por él; por ahora
  todas las rutas muestran la página de muestra, como antes.
- Vitest procesa solo el CSS de la paleta, para su test (excepción de archivos de T-029).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-029 | Variables de la identidad visual | `724098e` |
| T-030 | Fuentes y estilos cargados | `8aa1935` |
| T-031 | Proxy de la API en desarrollo | `401d44a` |
| T-032 | Enrutador | `d08b3e8` |
| T-033 | Aplicación con rutas | `36314f7` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 193 tests en verde. Arranca el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ en el navegador. Deberías ver la página de muestra con la fuente
Manrope, el lienzo gris azulado y los botones en forma de píldora. Cambia el tema de tu sistema
operativo a oscuro y recarga: el lienzo pasa a casi negro y el color de acción a azul claro. Pulsa
Tab hasta un botón: el foco se ve como un contorno de 3 px separado del botón.

Para probar el proxy, levanta además el backend con Docker:
```bash
docker compose -f docker/docker-compose.yml up -d db redis backend frontend
```
Pide la salud de la API a través del puerto del frontend:
```bash
curl -s http://localhost:5173/api/health/
```
Deberías ver `{"status": "ok"}`, la misma respuesta que da el backend en el puerto 8000.
