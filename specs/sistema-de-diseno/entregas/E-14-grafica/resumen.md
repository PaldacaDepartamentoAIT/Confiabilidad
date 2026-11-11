# Entrega E-14 · Gráfica de barras

Rama: `feat/sistema-de-diseno-grafica` (sale de `feat/sistema-de-diseno`) · PR: pendiente ·
Líneas de código y tests: 373 (límite: 400).

## Qué se hizo
- Hay una gráfica de barras de dos series dibujada en SVG propio, sin librería: la primera serie en el
  color principal y la segunda en gris, sólidas y sin borde. El lienzo es de 640 × 240 y se escala al
  ancho de su bloque; el área de trazado lleva una cuadrícula de 16 px detrás de las barras, números
  en el eje vertical cada 30 y el nombre de cada grupo debajo, centrado.
- El eje vertical va de 0 al siguiente múltiplo de 30 que cubra el mayor valor (mínimo 30). El ancho de
  cada grupo se ajusta al número de grupos: con seis son 96 px y las barras miden 30 px; con más
  grupos, las barras se reducen para seguir cabiendo.
- La gráfica es una imagen con un texto alternativo que describe los datos (lo escribe quien la usa).
- Si algún valor es negativo o no es un número, o no hay grupos, la escala lo rechaza y la gráfica no
  dibuja nada. El mensaje de vacío y la leyenda llegan en E-14b.
- El catálogo tiene una sección «Gráfica de barras» con las órdenes de trabajo de junio a noviembre.
  Verificado en un navegador real, en claro y oscuro: barras de 30 px, números en JetBrains Mono, meses
  en Manrope y, a 420 px, el lienzo se escala a 300 px de ancho.
- Esta parte salió de la gráfica completa (473 líneas), dividida por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-046 | Escala de la gráfica | `3e03b32` |
| T-047 | Gráfica de barras | `bed33cc` |
| T-048 | Catálogo: gráfica | ver historial de la rama |

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
Abre http://localhost:5173/ y baja hasta «Gráfica de barras»: verás las dos series, la cuadrícula y los
meses. Estrecha la ventana y la gráfica se encoge sin deformarse.

## Marco teórico
- **SVG y `viewBox`:** el SVG es un dibujo hecho con coordenadas, no con píxeles. El `viewBox` de
  640 × 240 fija el sistema de coordenadas y el navegador lo escala al ancho disponible, de modo que
  las proporciones se conservan en cualquier pantalla.
- **Eje en múltiplos de 30:** el máximo del eje se redondea hacia arriba al siguiente múltiplo de 30,
  para que las marcas sean siempre las mismas (0, 30, 60…) y la barra más alta no toque el borde.
- **Texto alternativo:** quien usa un lector de pantalla no ve las barras; el texto alternativo cuenta
  lo importante de los datos (qué se mide, entre qué fechas y cómo evolucionan).
