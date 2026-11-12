# Entrega E-16 · Comprobación visual

Rama: `feat/sistema-de-diseno-visual` (sale de `feat/sistema-de-diseno`) · PR: [#102](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/102) ·
Líneas de código y tests: 324 (límite: 400).

## Qué se hizo
- La comprobación visual deja de ser un script manual: ahora es un proyecto de pruebas (`pnpm
  --filter frontend test:visual`) que levanta la aplicación, la abre en un Chromium real y la mide.
  Va aparte de `pnpm test` porque necesita un navegador y es más lenta.
- **Comparación con las referencias (RF-028).** Mide los estilos calculados de cada pieza (tamaño de
  fuente, peso, familia, interlineado, espaciado de letras, color, fondo, bordes, radio, relleno y alto;
  ancho también en las de tamaño fijo) y exige igualdad exacta, sin tolerancia, entre el catálogo y las
  dos pantallas de referencia, en tema claro y oscuro. Falla al cambiar un valor de una pieza
  (comprobado con el relleno del bloque y el radio del botón).
- **Accesibilidad y contraste (RF-029).** Ejecuta `axe-core` en el navegador real, con la regla de
  contraste AA que jsdom no puede evaluar, en claro y oscuro, a 1280 y a 420 px. Falla si se pierde
  contraste (comprobado con el texto secundario del tema claro).
- **CI.** Un trabajo nuevo instala Chromium y ejecuta las pruebas visuales en cada PR.
- La primera comparación encontró diferencias reales, ya corregidas: la etiqueta de las casillas se
  veía en texto secundario en vez de en tinta (defecto de la aplicación); y las referencias declaraban
  la fuente como `Manrope` y la aplicación como `Manrope Variable` (el nombre del paquete), y el
  botón de menú de la referencia no fijaba su relleno. Esas dos se corrigieron en las referencias, no
  con una tolerancia.
- Se añadió la dependencia `playwright` (1.63.0, fija) a `devDependencies`, con permiso del usuario.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-052 | Playwright y proyecto de test visual | `5a2699e` |
| T-053 | Comparación con las referencias | `32795ed` |
| T-054 | Contraste y accesibilidad en ambos temas | `17d1306` |
| T-055 | Comprobación visual en CI | `8758cb3` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Descarga Chromium para Playwright (solo la primera vez):
```bash
pnpm --filter frontend exec playwright install chromium
```

Ejecuta las pruebas visuales:
```bash
pnpm --filter frontend test:visual
```
Deberías ver 14 pruebas en verde: 2 de humo, 4 de comparación con las referencias, 4 de accesibilidad y 4
de la función de diferencias.

Para ver que de verdad detectan un cambio, cambia en `frontend/src/components/Block.css` el relleno
`18px 20px 20px` por `19px 20px 20px` y vuelve a ejecutarlas: fallan las cuatro de comparación, con
«block.paddingTop: referencia=18px candidata=19px». Deshaz el cambio.

## Marco teórico
- **Estilo calculado:** el valor final que el navegador aplica a un elemento tras resolver todas las
  reglas, herencias y variables. Es lo que de verdad se ve, y por eso es lo que se compara.
- **Igualdad exacta sin tolerancia:** si se permitiera «casi igual», los pequeños desajustes se irían
  acumulando sin que nadie los notara. Con igualdad exacta, cada diferencia es una decisión consciente:
  se corrige la aplicación o se actualiza la referencia.
- **Contraste AA:** la proporción de luminosidad entre el texto y su fondo debe ser al menos 4,5:1 (3:1
  en texto grande) para que lo lea quien tiene baja visión. jsdom no calcula colores, por eso se mide en
  un navegador real.
