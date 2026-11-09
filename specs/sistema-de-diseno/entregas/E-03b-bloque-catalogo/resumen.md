# Entrega E-03b · Bloque y catálogo

Rama: `feat/sistema-de-diseno-bloque-catalogo` (sale de `feat/sistema-de-diseno-iconos`) · PR: pendiente ·
Líneas de código y tests: 350 (límite: 400).

## Qué se hizo
- Hay un componente de bloque en tres variantes: normal (superficie con borde gris), destacado (fondo
  secundario) y en alerta (relleno negro con texto blanco). Puede llevar cabecera con título,
  contador y acciones a la derecha, y puede ser una sección o un aparte, que el lector de pantalla
  anuncia con el nombre del título.
- La página de muestra tiene una sección nueva, «Bloques, etiquetas y formas de alarma», que exhibe
  los tres bloques, tres chips y las cuatro formas de alarma, en claro y oscuro.
- El contenido de ejemplo de esa sección es inventado y está escrito en español, marcado como tal
  para el lector de pantalla; no sigue el idioma activo.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-008 | Bloque | `fa1a2d2` |
| T-010 | Catálogo: bloques, chips y formas | `fc25cdc` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 36 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Bloques, etiquetas y formas de alarma» y pulsa el botón de
tema para ver los tres bloques, los chips y las cuatro formas en claro y oscuro.

## Marco teórico
- **Bloque (card) sin sombra:** la identidad es plana. Un bloque se separa del fondo con un borde
  gris de 1 px y esquinas de 4 px, sin sombras ni degradados; el destacado y el de alerta cambian
  el relleno, no el borde.
- **Región con nombre:** si un bloque es una `section` o un `aside` y tiene título, el lector de
  pantalla lo anuncia como zona con ese nombre y permite saltar a ella.
