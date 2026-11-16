# Resumen: sistema-de-diseno

Estado: validada con riesgo residual aceptado (16-nov-2026). Su PR a `main` debe fusionarse antes que los de
`casilla-con-documento` y `presentacion-registro`, que dependen de ella.

## Qué se hizo
La identidad visual de `docs/identidad-visual.md` (paleta Pizarra, tema claro y oscuro, tipografía y formas) se
convirtió en piezas reutilizables, y se aplicó a lo que ya existía (el registro y la página de muestra). Se
construyó en 16 entregas con sus subdivisiones:
- **Tema.** Paleta Pizarra, botón de tema con transición de 0,4 s, elección recordada y tema del sistema como
  punto de partida; iconos.
- **Piezas.** Bloque, botones principal y secundario, avisos y formas de alarma, campos de texto, casilla, botón
  del ojo de contraseña, menú de selección (selector propio, y el nativo en pantallas táctiles), indicadores,
  tabla, gráfica de barras con leyenda y rejilla de estado.
- **Diseños.** Pantallas públicas (barra superior con el nombre del sistema, idioma y tema; una columna centrada
  con un bloque) y pantallas con sesión (menú lateral que se contrae, barra superior con pestañas, buscador
  reducido y panel móvil), con el fundido al cambiar de sección.
- **Reserva de espacio del error** de los campos para que el formulario no cambie de altura.
- **Catálogo** (`/`) con todas las piezas y los dos diseños, y **comprobación automática contra la referencia**
  (`docs/referencia/*.html`) en Chromium, en claro y oscuro.
- **Pruebas.** 706 tests unitarios y 14 pruebas en Chromium (comparación, contraste y medidas).

## Cómo probarlo
Desde la raíz del repositorio, instala las dependencias:

```bash
pnpm install
```

Ejecuta los tests del frontend:

```bash
pnpm --filter frontend test
```

Deberías ver 706 tests en verde.

Ejecuta las pruebas en un navegador real (la primera vez, descarga Chromium):

```bash
pnpm --filter frontend exec playwright install chromium
```

```bash
pnpm --filter frontend test:visual
```

Deberías ver 14 pruebas en verde.

Levanta la aplicación:

```bash
pnpm --filter frontend dev
```

Abre http://localhost:5173/: es el catálogo con todas las piezas. Pulsa el botón de tema (cambia con una
transición de 0,4 s y se recuerda al recargar), contrae el menú lateral, reduce la ventana para ver el panel
móvil y el buscador reducido, y abre `/register` para ver el diseño público.

## Riesgo residual aceptado
La validación (13-nov-2026) dio NO CUMPLIDA con 14 de 31 requisitos con evidencia completa, y el 16-nov-2026 el
usuario decidió cerrar sin tareas de corrección. Los riesgos aceptados:
1. **RF-004, movimiento reducido (defecto de código real).** Con la preferencia del sistema activa, el cambio de
   tema sigue animando 0,4 s: `.theme-anim *` de `ThemeButton.css`, con `!important` y más especificidad, gana a
   la regla global de `base.css`. Impacto bajo, probabilidad media. Corrección posible: un `@media
   (prefers-reduced-motion: reduce)` en `ThemeButton.css`.
2. **D-12 (defecto de código).** `base.css` aún estila `a`, `h1, h2` y `label, small`, contra la decisión de que
   solo tenga reinicio, fuente, foco y movimiento reducido. Quitarlo exige una clase propia para el enlace
   «volver al formulario».
3. **RF-030, idiomas (plan).** `Table`, `BarChart` y `StatusGrid` reciben sus textos por props y el catálogo los
   muestra siempre en español; el plan no decidió quién traduce esos textos. Propuesta pendiente: precisar en la
   spec que los da cada pantalla.
4. **Falta de pruebas que fijen el CSS (15 RF).** Medidas del menú lateral, duraciones de las animaciones, hover
   y foco, variantes de bloque e indicador y filas de 44 px: el CSS cumple, pero una regresión no fallaría.
5. **RF-028, comparación.** Mide 26 piezas en reposo; no compara el aviso ni la gráfica, ni variantes y estados.
   Corregirlo exige tocar las referencias HTML, que requieren tu autorización.
6. **RF-031.** Sin prueba del `<select>` nativo con un valor elegido.
7. **Documentación.** Ocho líneas de «Cómo probarlo» de `tasks.md` llevan comandos en línea y no en bloque.

## Marco teórico
- **Sistema de diseño.** Un conjunto de piezas con sus reglas visuales (colores, tamaños, estados) que se
  reutilizan en todas las pantallas, para que no cada una reinvente su aspecto.
- **Tokens (variables de diseño).** Valores con nombre (`--primary`, `--bg`…) definidos una vez por tema; las
  piezas los usan en lugar de colores sueltos, de modo que cambiar de tema es cambiar los valores de los tokens.
- **Comparar contra una referencia.** Las pantallas HTML aprobadas son la verdad visual; un test mide en
  Chromium cada pieza real y la de la referencia y exige que sean iguales, para que un cambio de CSS no desvíe el
  diseño sin que nadie lo vea.
- **Reserva de espacio del error.** Se deja siempre una línea libre bajo cada campo; así, cuando aparece el
  mensaje de error, el formulario no salta.
- **Movimiento reducido.** Una preferencia del sistema operativo de quien se marea con las animaciones; la
  aplicación debe respetarla en todos sus cambios, incluidos los que añade un componente.
- **Especificidad del CSS.** Si dos reglas chocan, gana la más específica, no la que parece más general; por eso
  un `*` con `!important` en `base.css` pierde contra `.theme-anim *`.
