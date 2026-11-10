# Entrega E-10 · Diseño con sesión

Rama: `feat/sistema-de-diseno-con-sesion-base` · PR: pendiente ·
Líneas de código y tests: 259 (límite: 400).

## Qué se hizo
- Hay un diseño para las pantallas con sesión iniciada: el menú lateral a la izquierda, con la
  altura de la pantalla; a su lado, una barra superior de 64 px con una línea inferior gris y,
  debajo, el contenido, con un margen de 22 px y 18 px entre bloques. La barra tiene un hueco para
  lo que cada pantalla quiera poner (más adelante, las pestañas y el buscador).
- El diseño recibe los elementos del menú, el elemento actual, el usuario y el hueco de la barra, y
  los reparte. La barra es el `banner` de la página y el contenido, su `main`.
- Existe una variante «embebida», que convierte la barra y el contenido en bloques sin significado
  de zona, para enseñar el diseño dentro de otra página que ya tiene su propio `banner` y `main`
  (el catálogo).
- La página de muestra sustituye la sección del menú lateral suelto por una nueva, «Diseño con
  sesión», con una pantalla de ejemplo completa (menú, barra y un bloque de contenido). Verificado
  en un navegador real: menú de 232 px, barra de 64 px y contenido a su lado, en claro y oscuro.
- El panel superpuesto del menú en pantallas pequeñas y el botón de la barra que lo abre llegan en
  E-10b y E-10c. La entrega completa medía 752 líneas y se dividió en tres por la regla de
  `AGENTS.md`; la parte del panel (E-10b) no se ve sola.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-033 | Diseño con sesión | `4e52e7c` |
| T-034 | Catálogo: diseño con sesión | `4a8a8b4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 45 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Diseño con sesión» y comprueba la pantalla de ejemplo: menú
a la izquierda, barra superior vacía y un bloque de contenido. Contrae el menú con su botón y cambia
el tema para verlo en claro y oscuro.

## Marco teórico
- **Diseño con sesión frente a diseño público:** las pantallas sin sesión solo tienen una barra con
  el nombre y los botones de idioma y tema; las pantallas con sesión suman el menú lateral y la barra
  de secciones. Son dos envoltorios distintos y cada pantalla elige el suyo.
- **Hueco de la barra (slot):** el diseño reserva un sitio en la barra superior sin decidir qué va
  ahí; cada pantalla lo rellena con sus pestañas y su buscador.
