# Entrega E-02 · Aspecto del modal y foco

Rama: `feat/casilla-con-documento-aspecto-modal` (sale de `feat/casilla-con-documento`) · PR: pendiente ·
Líneas de código y tests: 209 (límite: 400).

## Qué se hizo
- El modal de documento tiene ya el aspecto de la guía: una cortina negra al 50 % sobre toda la pantalla (la
  misma en claro y oscuro) y una caja con el relleno negro del sistema (`#1b1e22` en claro y `#000000` en
  oscuro), texto blanco, borde de 1 px en el color de las líneas y radio de 4 px, centrada.
- Mide 640 px de ancho como máximo y, por debajo de 700 px de pantalla, el ancho completo menos 32 px; el alto
  máximo es el 80 % del alto visible, sin pasar de ese alto menos 32 px. Solo se desplaza el contenido: la «×»
  y la casilla del pie siguen a la vista.
- Mientras está abierto, la página de detrás no se desplaza. Aparece con un fundido de 0,2 s (la caja y la
  cortina).
- Los enlaces del documento son azul grisáceo (`#7f94b5`) y sin subrayado, y la etiqueta de la casilla del pie
  se lee en blanco.
- Al cerrar el modal —con la «×», Escape o un clic en la cortina—, el foco vuelve al elemento que lo abrió. Era
  un defecto real, detectado por la prueba en Chromium de la entrega siguiente (E-02b).
- La guía (`docs/identidad-visual.md`) tiene una sección nueva, «Modal de documento», y una fila en la tabla de
  movimiento.
- Esta parte salió de una entrega de 425 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-006 | Aspecto del modal según la guía | `bac17f0` |
| T-016 | Corrección: el modal devuelve el foco al elemento que lo abrió | `fefbe93` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 60 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Documento en un modal» y pulsa «Abrir el documento»: verás la cortina
oscura, la caja negra y los enlaces en azul grisáceo. Cierra con la «×», con Escape o pulsando fuera de la
caja; el foco vuelve al botón. Prueba también con la ventana estrecha (por debajo de 700 px la caja ocupa casi
todo el ancho).

## Marco teórico
- **Relación de contraste de un enlace sin subrayado:** si un enlace no se subraya, solo el color lo distingue
  del texto, y ese color debe contrastar al menos 3:1 con el texto que lo rodea (y 4,5:1 con el fondo). Por eso
  los enlaces del modal no son blancos.
- **Devolver el foco:** al cerrar un diálogo, quien usa el teclado o un lector de pantalla debe volver al punto
  donde estaba; si el foco se pierde, vuelve al principio de la página.
