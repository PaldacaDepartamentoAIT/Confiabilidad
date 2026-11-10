# Entrega E-08 · Diseño público y pantallas de registro y acceso con él

Rama: `feat/sistema-de-diseno-publico-registro` · PR: pendiente ·
Líneas de código y tests: 373 (límite: 400).

## Qué se hizo
- Hay un diseño para las pantallas sin sesión: una barra superior de 64 px, fija arriba y con una
  línea inferior gris, con el nombre del sistema a la izquierda (en negrita, subrayado, que sigue el
  idioma: «Confiabilidad», «Confiabilidade» o «Reliability») y, a la derecha, el botón de idioma y el
  de tema. No hay menú lateral. El contenido va debajo, con su propio `<main>`. El menú de idioma
  se abre alineado al borde derecho de la barra.
- Las pantallas de registro (formulario, verificación de código, enlace no válido y cuenta creada)
  usan ese diseño, sin cambiar su flujo, sus textos ni sus validaciones: los tests previos de
  registro pasan sin cambios. El selector de idioma de tres botones desaparece de estas pantallas,
  porque el botón de idioma de la barra lo sustituye.
- Verificado en un navegador real con la API simulada: la barra mide 64 px a todo el ancho, con
  borde inferior de 1 px, y el menú de idioma sale a la derecha, en claro y oscuro.
- Dos reglas son transitorias y se retiran con la limpieza de `base.css` (T-051): un margen negativo
  que compensa el relleno provisional del `body` y las cajas con borde que `base.css` aún pone a
  `main`, `form` y `section`.
- La página de muestra todavía no usa este diseño: llega en E-08b. La entrega original medía 531
  líneas, casi todas de reindentar las páginas al envolverlas, y se dividió por la regla de
  `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-026 | Diseño público | `0a8d268` |
| T-027 | Registro y acceso usan el diseño público | `9a446c3` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 43 archivos de test en verde.

Levanta la aplicación con el backend (el registro carga los países de la API):
```bash
docker compose -f docker/docker-compose.yml up
```
Abre http://localhost:5173/register: debe verse la barra superior con el nombre y los botones de
idioma y tema. Cambia de idioma y de tema desde ella, y recorre también `/register/continue` y
`/register/done`.

## Marco teórico
- **Diseño (layout) como envoltorio:** en lugar de repetir la barra superior en cada pantalla, una
  sola pieza la dibuja y las pantallas se limitan a meterse dentro. Si la barra cambia, cambia en
  todas a la vez.
- **Región de la página (`banner`, `main`):** la barra superior es el `banner` y el contenido, el
  `main`; el lector de pantalla permite saltar de una a otra. Por eso el diseño no pinta el `main`:
  cada pantalla pone el suyo, y solo debe haber uno.
