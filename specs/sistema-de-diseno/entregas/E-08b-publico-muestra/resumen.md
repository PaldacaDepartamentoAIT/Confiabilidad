# Entrega E-08b · Página de muestra con el diseño público

Rama: `feat/sistema-de-diseno-publico-muestra` (sale de `feat/sistema-de-diseno-publico-registro`) · PR: pendiente ·
Líneas de código y tests: 158 (límite: 400).

## Qué se hizo
- La página de muestra (el catálogo de piezas) usa el diseño público: barra superior con el nombre
  del sistema y los botones de idioma y de tema. Su botón de tema propio, que estaba bajo el
  selector de idioma, desaparece porque el de la barra lo sustituye (no debe haber dos). El selector
  de idioma de tres botones se conserva en la página porque es una de las piezas que muestra.
- El orden del teclado empieza ahora por la barra (idioma, tema), sigue por el selector de tres
  botones y continúa por los campos del formulario de ejemplo. Dos tests se ajustaron por eso: el
  del orden del teclado y el que cambia de idioma con el teclado en `App.test.tsx`.
- Esta parte salió de la entrega del diseño público, que medía 531 líneas (casi todas de reindentar
  las páginas al envolverlas).

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-028 | Página de muestra en el diseño público | `c7052ed` |

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

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/: debe verse la barra superior con el nombre y los botones de idioma y
tema, y debajo el catálogo. Pulsa el botón de tema de la barra y comprueba que cambia toda la página.

## Marco teórico
- **Un solo botón de tema:** el tema es una decisión de toda la aplicación, no de una pantalla; por
  eso vive en la barra común y no se repite en cada página.
