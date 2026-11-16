# Entrega E-11 · Pestañas en la barra superior

Rama: `feat/sistema-de-diseno-pestanas` · PR: [PaldacaDepartamentoAIT/Confiabilidad#88](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/88) ·
Líneas de código y tests: 375 (límite: 400).

## Qué se hizo
- Hay unas pestañas para la barra superior de las pantallas con sesión. Cada pestaña es un botón de
  36 px; la activa va en tinta y el resto en texto secundario, y todas se tiñen un poco al pasar el
  cursor. Bajo la activa hay una línea de 2 px en el color principal, con 12 px de margen a cada
  lado, que se desplaza hasta la pestaña nueva en 0,25 s cuando cambia la selección.
- Con el teclado, solo la pestaña activa está en el orden de tabulación; las flechas izquierda y
  derecha pasan a la anterior o a la siguiente (dando la vuelta al llegar al extremo), y Inicio y Fin
  van a la primera y a la última. La pestaña a la que se llega queda seleccionada y con el foco.
- Cada pestaña lleva los identificadores (`aria-controls`) que enlazan con su panel, de modo que el
  lector de pantalla anuncia «pestaña 2 de 4».
- La pantalla de ejemplo del catálogo («Diseño con sesión») tiene ahora tres pestañas (Resumen,
  Inventario y Alarmas) en el hueco de su barra superior, cada una con su panel, y cambiar de
  pestaña con el ratón o las flechas muestra su sección. Verificado en un navegador real, en claro y
  oscuro: la línea queda a 12 px del borde de la pestaña con su ancho menos 24 px.
- Esta entrega nació como parte de la barra superior con pestañas y buscador (654 líneas); por el
  límite de 400 se dividió en esta y E-11b (buscador y barra completa). T-064 nació de esa división.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-035 | Pestañas | `c177b32` |
| T-064 | Catálogo: pestañas | `d9c345c` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 47 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Diseño con sesión», pulsa una pestaña con el ratón y mira
cómo la línea se desliza; luego llega con Tab a la pestaña activa y muévete con las flechas, Inicio y
Fin.

## Marco teórico
- **Pestañas con activación automática:** al moverse con las flechas, la pestaña se selecciona al
  momento y su contenido se muestra, sin tener que pulsar Intro. Es el comportamiento habitual y
  el de la referencia.
- **Orden de tabulación en grupo (`tabindex` itinerante):** solo la pestaña activa se alcanza con
  Tab; el resto se recorre con las flechas. Así un grupo de pestañas ocupa una sola parada del
  teclado.
