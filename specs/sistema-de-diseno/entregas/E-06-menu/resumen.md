# Entrega E-06 · Menú desplegable compartido

Rama: `feat/sistema-de-diseno-menu` · PR: pendiente ·
Líneas de código y tests: 474 (límite: 400; Excepción aprobada hasta 500, ver abajo).

## Qué se hizo
- Hay un menú desplegable compartido, la base del selector propio, del botón de idioma y del
  selector de pestañas que llegan después. El disparador lo pinta quien lo usa; el menú se ocupa de
  abrirse bajo él (a 4 px), mostrar las opciones, marcar la seleccionada (en negrita y con un chevron
  «>») y resaltar la activa.
- Con el ratón se abre con un clic, elige con otro clic, resalta al pasar el cursor y se cierra al
  pulsar fuera o al volver a pulsar el disparador. Con el teclado se abre con Flecha abajo, Flecha
  arriba, Intro o Espacio; se mueve con las flechas (sin dar la vuelta), Inicio y Fin; elige con
  Intro o Espacio y se cierra con Escape o al salir del foco. El foco no sale nunca del disparador.
- Se abre con una animación de 0,18 s (fundido y 6 px hacia abajo) y se cierra sin animación. Para
  el lector de pantalla es una lista desplegable (`combobox` con `listbox`) con la opción activa
  indicada en cada momento.
- Esta entrega no muestra nada nuevo en pantalla: el botón de idioma y la sección del catálogo son
  E-06b. La entrega original medía 725 líneas y, por el límite de 400, se dividió por la regla de
  `AGENTS.md`.
- **Excepción:** el menú con su teclado, su ratón, su animación y sus tests es un solo
  comportamiento y no se puede dividir sin dejar una versión inservible; supera 400 líneas y
  se queda en 474, por debajo de las 500 de la excepción. No hay forma de que esta entrega enseñe
  algo en pantalla sin pasarse de 500, así que la parte visible va en E-06b.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-019 | Menú desplegable compartido | `64fd9f0` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 40 archivos de test en verde, entre ellos `src/components/menu/Menu.test.tsx` (18 tests).

## Marco teórico
- **Combobox de solo selección (WAI-ARIA):** patrón de accesibilidad para una lista desplegable.
  El foco se queda en el botón que la abre y el lector de pantalla recibe, en cada momento, cuál es
  la opción resaltada mediante `aria-activedescendant`. Así se maneja con teclado sin mover el foco.
- **Disparador propio:** el menú no dibuja el botón que lo abre; lo recibe de quien lo usa. Eso
  permite que el mismo menú sirva para un selector de formulario, un botón del menú lateral y el
  selector de pestañas sin repetir el comportamiento.
