# Entrega E-13 · Indicadores

Rama: `feat/sistema-de-diseno-indicadores` (sale de `feat/sistema-de-diseno`) · PR: [#93](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/93) ·
Líneas de código y tests: 164 (límite: 400).

## Qué se hizo
- Hay un indicador: un bloque con una etiqueta, una cifra grande (28 px, números alineados) y una
  ayuda opcional. Tiene tres variantes: normal, destacado (fondo secundario) y en alerta (fondo negro,
  etiqueta y ayuda en blanco y la cifra en el color de la prioridad P1).
- Los indicadores se distribuyen en una rejilla de columnas automáticas de 190 px como mínimo y 18 px de
  separación.
- El catálogo tiene una sección «Indicadores» con los cuatro de la referencia. Verificado en un
  navegador real: la cifra mide 28 px y a 1000 px de ancho caben cuatro columnas.
- Esta parte salió de «Indicadores y tabla» (478 líneas); la tabla es la entrega E-13b, por la regla de
  división de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-043 | Indicador y su rejilla | `16980b2` |
| T-045 | Catálogo: indicadores | `78aa11b` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 51 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y baja hasta «Indicadores»: verás cuatro indicadores, uno destacado y uno
en alerta. Estrecha la ventana y las columnas pasan a ser menos.

## Marco teórico
- **Rejilla automática (`auto-fit` con mínimo de 190 px):** el navegador mete tantas columnas como
  quepan sin que ninguna baje de 190 px, y reparte el sobrante entre ellas. No hace falta ningún
  punto de corte para pantallas pequeñas.
- **Cifras tabulares (`tabular-nums`):** todos los dígitos ocupan el mismo ancho, de modo que las
  cifras de varios indicadores quedan alineadas y no «bailan» al cambiar de valor.
