# Entrega E-14b · Leyenda y mensaje de vacío de la gráfica

Rama: `feat/sistema-de-diseno-grafica-leyenda` (sale de `feat/sistema-de-diseno`, con E-14 ya fusionada) · PR: pendiente ·
Líneas de código y tests: 262 (límite: 400).

## Qué se hizo
- La gráfica de barras lleva ahora su leyenda: dos muestras de 12 × 12 px (principal y gris) con el
  nombre de cada serie, separadas 16 px y alineadas a la derecha, encima del lienzo.
- Si no hay datos, o algún valor es negativo o no es un número, la gráfica muestra un mensaje de vacío
  en lugar del dibujo (y sin leyenda).
- El catálogo muestra la gráfica con su leyenda y, debajo, una gráfica sin datos con su mensaje.
- Esta parte salió de la gráfica completa (473 líneas), dividida por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-068 | Leyenda y mensaje de vacío de la gráfica | `ca56c24` |
| T-069 | Catálogo: leyenda y gráfica sin datos | `ca56c24` |

Las dos tareas comparten commit porque las propiedades nuevas son obligatorias y el catálogo debía
pasarlas para que el tipado no se rompiera.

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 54 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Gráfica de barras»: verás la leyenda sobre la gráfica y, debajo,
un bloque «Gráfica sin datos» con su mensaje.

## Marco teórico
- **Estado vacío:** mostrar un mensaje en lugar de un dibujo en blanco evita que parezca un error y
  explica por qué no hay nada. Los datos no válidos se tratan igual para no dibujar barras engañosas.
