# Entrega E-12c · Buscador reducido en pantallas pequeñas

Rama: `feat/sistema-de-diseno-buscador-reducido` (sale de `feat/sistema-de-diseno-pestanas-selector`) · PR: pendiente ·
Líneas de código y tests: 234 (límite: 400).

## Qué se hizo
- En pantallas de menos de 560 px, el buscador de la barra superior se reduce a un botón con lupa
  de 36 × 36 px. Al pulsarlo, el campo (de 220 px) se despliega sobre las pestañas, que quedan
  ocultas, y recibe el foco. Escape lo cierra y devuelve el foco al botón. Si la pantalla se
  ensancha con el campo abierto, se cierra; en pantalla ancha no hay botón y el campo se ve siempre.
- El botón se llama igual que el campo, salvo que la pantalla le dé otro nombre.
- Un fallo que solo se veía en un navegador real quedó corregido antes de entregar: el botón está
  oculto mientras el campo está abierto, y el foco no puede llegar a un elemento oculto, así que el
  foco vuelve después de que la pantalla se redibuje.
- Verificado en un navegador real a 500 px: cerrado es un botón de 36 × 36 px; abierto, el campo
  cubre las pestañas; Escape lo cierra y el foco queda en el botón.
- Esta parte salió de las pestañas adaptables (796 líneas), dividida en tres por la regla de
  `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-041 | Buscador reducido en pantallas pequeñas | `8911511` |

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
Abre http://localhost:5173/, baja hasta «Diseño con sesión» y estrecha la ventana por debajo de 560 px:
el buscador pasa a ser una lupa; púlsala, escribe algo y cierra con Escape.

## Marco teórico
- **Despliegue sobre las pestañas:** el campo no se queda en la barra porque no cabe; se coloca
  encima de las pestañas, que se ocultan mientras está abierto, y al cerrarlo todo vuelve.
- **Foco en un elemento oculto:** un elemento con `visibility: hidden` no puede recibir el foco, por
  eso el foco se devuelve al botón solo cuando ya es visible de nuevo.
