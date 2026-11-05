# Entrega E-01 · Barra superior con idioma

Rama: `feat/registro-diseno-visual-barra-idioma` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#60](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/60) ·
Líneas de código y tests: 935 (límite: 400; aceptado por el usuario, ver «Excepción» de E-01 en
`tasks.md`).

## Qué se hizo
- **Guía visual ampliada** (`docs/identidad-visual.md`, T-001; ajustada en `ecc38b0` con la pista
  de teclado y los pasos pendientes punteados): la barra superior, el botón con
  menú, el indicador de pasos, los campos, el «?», el selector propio, la ventana de documento, la
  zona de mensajes y el asistente por pasos, con las excepciones que eligió el usuario (indicador en
  círculos de relleno fuerte, asterisco y errores en alarma P1, fondo opaco de la ventana, radio de
  4 px).
- **Botón con menú** (`MenuButton`, T-003): botón circular que despliega opciones exclusivas.
  Recorrer con las flechas no elige; solo Intro, Espacio o clic. Escape, Tab, un clic fuera o mover
  el foco lo cierran sin cambiar nada. Al desplegarse muestra una pista de teclado («↑ ↓ moverte ·
  Intro elegir · Esc cerrar», T-044 y T-045), solo visual: el lector de pantalla ya anuncia cómo se
  usa un menú.
- **Menú de idioma** (`LanguageMenu`, T-002 y T-004): el botón muestra «ES», «EN» o «PT» y el menú,
  cada idioma con su nombre en ese idioma. Elegir cambia el idioma sin recargar, lo recuerda y deja
  el foco en el botón.
- **Barra superior en toda la aplicación** (`TopBar`, T-005 y T-006): una sola barra fuera del
  contenido principal, en la página de muestra y en todas las del registro, que ya no pintan su
  propio selector.

El menú de tema llega en E-02; el aspecto de la barra se completa con él.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Guía visual ampliada | `20b5623`, `3a16e4a` |
| T-002 | Textos de la barra superior | `e5bff59` |
| T-003 | Botón con menú | `41e9013` |
| T-004 | Menú de idioma | `5a7f1de` |
| T-005 | Barra superior en toda la aplicación | `2361697` |
| T-006 | Las pantallas dejan de pintar su selector | `dcaea75` |
| T-044 | Texto de la pista de teclado | `90c4c6e` |
| T-045 | Pista de teclado en el menú | `74de67b` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde. Para verlo en el navegador, levanta el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y, arriba, pulsa el botón «ES» (o el del idioma que tengas). Deberías
ver el menú con «Español», «Português (Brasil)» y «English»; elige «English» y la página cambia de
idioma sin recargar. Prueba también con el teclado: Tab hasta el botón, Intro para abrir, flechas
para moverte (el idioma no cambia), Intro para elegir y Escape para cerrar sin elegir. Recarga: el
idioma elegido se mantiene. En http://localhost:5173/register verás la misma barra.

## Marco teórico
- **Por qué el menú no cambia el idioma al moverse con las flechas.** Cambiar el idioma de toda la
  página es un cambio de contexto; si ocurriera con cada flecha, quien usa teclado o lector de
  pantalla perdería el sitio a cada pulsación (WCAG 3.2.2). Por eso las flechas solo resaltan y el
  cambio llega al elegir con Intro, Espacio o clic.
