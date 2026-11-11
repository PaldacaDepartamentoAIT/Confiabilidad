# Entrega E-12 · Fundido entre secciones de las pestañas

Rama: `feat/sistema-de-diseno-fundido` · PR: [#90](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/90) ·
Líneas de código y tests: 177 (límite: 400).

## Qué se hizo
- Hay un panel de pestaña: la sección que cada pestaña muestra. Solo el panel de la pestaña activa
  es visible; los demás quedan ocultos (también para el lector de pantalla). Cuando una sección pasa a
  ser la activa, aparece con un fundido de 0,2 s; la primera vez que se carga la página no hay
  fundido. Con el movimiento reducido en el sistema operativo, el cambio es inmediato.
- Cada panel tiene el identificador y el nombre (`aria-labelledby`) de su pestaña, de modo que el
  lector de pantalla anuncia «panel de la pestaña Inventario».
- La pantalla de ejemplo del catálogo («Diseño con sesión») usa estos paneles: al pulsar una pestaña,
  la sección nueva aparece con fundido. Verificado en un navegador real: la opacidad pasa de 0 a 1 en
  unos 0,2 s y solo queda un panel visible.
- Esta entrega nació como parte de las pestañas adaptables (796 líneas); por el límite de 400 se
  dividió en tres: esta (fundido), E-12b (selector de pestañas cuando no caben) y E-12c (buscador
  reducido en pantallas pequeñas). El catálogo ya muestra también esas dos cosas cuando lleguen.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-040 | Cambio de sección con fundido | `fe6d98b` |
| T-042 | Catálogo: pestañas completas | `dc788d3` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 50 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Diseño con sesión» y pulsa las pestañas: cada sección nueva
aparece con un fundido suave.

## Marco teórico
- **Panel de pestaña (`tabpanel`):** la sección que se muestra al elegir una pestaña. Está enlazada
  con ella por sus identificadores, y los paneles inactivos se ocultan del todo (no solo se tapan).
- **Fundido solo al cambiar:** si el panel se animara también al cargar la página, la pantalla
  parpadearía al entrar. Por eso el fundido solo ocurre cuando el panel pasa de oculto a visible.
