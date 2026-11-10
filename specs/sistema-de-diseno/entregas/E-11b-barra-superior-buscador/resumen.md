# Entrega E-11b · Buscador y barra superior completa

Rama: `feat/sistema-de-diseno-barra-superior-buscador` · PR: [PaldacaDepartamentoAIT/Confiabilidad#89](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/89) ·
Líneas de código y tests: 287 (límite: 400).

## Qué se hizo
- Hay un buscador para la barra superior: un campo de 220 × 36 px con una lupa a la izquierda,
  con el aspecto de un campo de formulario (borde de 1 px, 2 px con el foco). Es solo visual: se puede
  escribir en él, pero no filtra nada ni envía ni avisa de nada; lo que haga lo decide cada pantalla
  que lo use. Su nombre accesible y su texto de reserva los da la pantalla.
- Hay una barra superior completa, que va en el hueco de la barra del diseño con sesión: las
  pestañas a la izquierda, ocupando el sitio que deja el buscador, y el buscador a la derecha.
- La pantalla de ejemplo del catálogo («Diseño con sesión») usa esa barra: pestañas y buscador.
  Verificado en un navegador real, en claro y oscuro: buscador de 220 × 36 px y pestañas con su
  línea de 2 px.
- Esta parte salió de la entrega de la barra superior (654 líneas), dividida por la regla de
  `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-036 | Buscador | `28102b6` |
| T-037 | Barra superior | `b58cabe` |
| T-038 | Catálogo: barra superior | `2d1b787` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 49 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Diseño con sesión» y comprueba la barra: las pestañas a la
izquierda y el buscador a la derecha. Escribe en el buscador y comprueba que no pasa nada más.

## Marco teórico
- **Buscador solo visual:** el componente dibuja el campo, pero no decide qué se busca ni cómo; así
  cada pantalla (activos, alarmas…) lo conecta a lo suyo cuando exista esa funcionalidad.
- **Texto de reserva y nombre accesible:** el campo muestra «Buscar…» como pista, pero un lector de
  pantalla necesita un nombre propio; ambos vienen de la pantalla, ya traducidos.
