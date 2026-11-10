# Entrega E-10c · Botón de menú de la barra que abre el panel

Rama: `feat/sistema-de-diseno-con-sesion-boton` · PR: [PaldacaDepartamentoAIT/Confiabilidad#87](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/87) ·
Líneas de código y tests: 143 (límite: 400).

## Qué se hizo
- En pantallas de menos de 768 px, la barra superior del diseño con sesión muestra, a la izquierda,
  un botón de menú («Abrir menú»). Al pulsarlo, el menú lateral se abre como panel superpuesto y el
  foco pasa a su botón «Cerrar menú». Pulsarlo de nuevo, pulsar fuera, Escape, el botón de la
  cabecera del menú o elegir un elemento lo cierran; con el botón de la cabecera y con Escape el
  foco vuelve al botón de la barra. En pantallas anchas ese botón no se ve.
- El botón señala al menú con `aria-controls` y anuncia si está abierto con `aria-expanded`.
- La sección «Diseño con sesión» de la página de muestra lo permite: en una ventana estrecha se puede
  abrir y cerrar el panel. Verificado en un navegador real a 420 px: el menú cerrado queda fuera de la
  pantalla, al abrirlo entra con el foco en «Cerrar menú», Escape lo cierra devolviendo el foco al
  botón y un clic fuera lo cierra.
- Con esta entrega queda completo el diseño con sesión y el menú móvil. La entrega original medía 752
  líneas y se dividió en tres por la regla de `AGENTS.md` (E-10, E-10b y esta).

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-063 | Botón de menú en la barra y apertura del panel | `35311fc` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 46 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y estrecha la ventana por debajo de 768 px (o activa la emulación de un
móvil en las herramientas del navegador). En «Diseño con sesión», pulsa «Abrir menú», comprueba que el
panel entra desde la izquierda y ciérralo con Escape.

## Marco teórico
- **`aria-controls` y `aria-expanded`:** el botón dice qué elemento controla y si está desplegado, de
  modo que el lector de pantalla anuncia «menú, contraído» o «expandido» al llegar a él.
