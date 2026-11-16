# Plan: sistema-de-diseno
Estado: aprobado

## Módulos
Todos viven en `frontend/src/`; no se toca `backend/` ni `desktop/`.

### M-01 Tokens y base (`styles/tokens.css`, `styles/base.css`, `styles/tokens.test.ts`)
Responsabilidad: variables de la paleta Pizarra con los nombres de las referencias (`--bg`, `--surface`, `--ink`, `--text2`, `--gray`, `--grid`, `--primary`, `--secondary`, `--p1`, `--p2`, `--warn`, `--black-fill`, `--menu-btn-*`) para claro y oscuro; reglas generales (reinicio, fuente, foco visible, movimiento reducido). Sustituye a Niebla marina. `base.css` deja de estilar elementos sueltos (`button`, `input`, `section`…).
RF: RF-001, RF-004, RF-029

### M-02 Tema (`theme/theme.ts`, `theme/ThemeButton.tsx`)
Responsabilidad: leer el tema guardado (con almacenamiento inyectable, como `i18n/language.ts`), validarlo, aplicarlo en `<html data-theme>` antes del primer render y alternarlo con transición de 0,4 s; botón de tema para barra y menú.
RF: RF-001, RF-002, RF-003

### M-03 Iconos y formas (`icons/`)
Responsabilidad: iconos de `lucide-react` (16 px, trazo 2) reexportados por nombre; formas de alarma propias (cuadrado, triángulo, rombo, cuadrado vacío) como componentes SVG.
RF: RF-020, RF-025

### M-04 Menú desplegable compartido (`components/menu/`)
Responsabilidad: panel emergente con animación de 0,18 s, cierre con Escape y clic fuera, y navegación con flechas; lo usan el selector propio, el botón de idioma y el selector de pestañas.
RF: RF-011, RF-016

### M-05 Diseños y menú lateral (`layouts/PublicLayout.tsx`, `layouts/AppLayout.tsx`, `layouts/Sidebar.tsx`, `layouts/useMediaQuery.ts`)
Responsabilidad: diseño público (barra con nombre, idioma y tema) y diseño con sesión (menú, barra superior, contenido); menú con elementos como datos, contador, activo, pie (tema, idioma, usuario con acción opcional), contraer/expandir con `aria-expanded`, panel superpuesto y retorno del foco al cerrar en menos de 768 px.
RF: RF-005, RF-006, RF-007, RF-008, RF-009

### M-06 Barra superior y pestañas (`layouts/TopBar.tsx`, `layouts/Tabs.tsx`, `layouts/SearchBox.tsx`)
Responsabilidad: pestañas con teclado, línea activa que se desplaza, selector cuando no caben, buscador solo visual (botón con lupa por debajo de 560 px) y fundido de 0,2 s entre secciones.
RF: RF-010, RF-011, RF-012, RF-013

### M-07 Bloque, botón, avisos y chip (`components/Block.tsx`, `components/Button.tsx`, `components/Notice.tsx`, `components/AlarmNotice.tsx`, `components/Chip.tsx`)
Responsabilidad: bloque en tres variantes con cabecera; botón principal/secundario restilizado sin cambiar su lógica; avisos y chip.
RF: RF-014, RF-018, RF-019, RF-020, RF-023

### M-08 Campos (`components/fields/*`)
Responsabilidad: restilizar `TextField`, `PasswordField`, `CodeField`, `Checkbox` y la leyenda de obligatorios sin cambiar su comportamiento; `SelectField` con la misma API, que muestra el selector propio (disparador `<button role="combobox" name value>`, lista de opciones sobre M-04) o el `<select>` nativo si el puntero principal es táctil.
RF: RF-015, RF-016, RF-017, RF-031

### M-09 Datos (`components/data/Indicator.tsx`, `Table.tsx`, `BarChart.tsx`, `chartScale.ts`, `StatusGrid.tsx`)
Responsabilidad: indicador y su rejilla, tabla con estados vacíos, gráfica de barras SVG con eje automático (función pura de escala) y rejilla de estado con leyenda.
RF: RF-021, RF-022, RF-024, RF-025

### M-10 Botón de idioma (`components/LanguageButton.tsx`, `i18n/locales/*`)
Responsabilidad: botón con el código del idioma activo que abre un menú (M-04) con los tres idiomas, reutilizando la lógica de `LanguageSwitcher`; claves nuevas de las piezas en los tres idiomas.
RF: RF-005, RF-007, RF-030

### M-11 Aplicación a lo existente y catálogo (`registration/*`, `showcase/ShowcasePage.tsx`, `App.tsx`)
Responsabilidad: las pantallas de registro y de acceso por código usan el diseño público y las piezas nuevas sin cambiar su flujo; la página de muestra pasa a ser el catálogo de todas las piezas, en ambos diseños, con elementos de ejemplo.
RF: RF-026, RF-027

### M-12 Comprobación contra la referencia (`frontend/visual/*`, `docs/referencia/*`)
Responsabilidad: contrato `data-ui` (cada pieza lo lleva en su elemento raíz); test con Playwright que abre el catálogo y las referencias en claro y oscuro y compara, con igualdad exacta, las propiedades de RF-028; comprobación de contraste con `axe-core` en ambos temas. Corre con `pnpm --filter frontend test:visual`.
RF: RF-028, RF-029

## Modelo de datos
Sin base de datos. Un valor en el navegador: la clave `theme` (`light` | `dark`) en `localStorage`, junto a la de idioma ya existente. Un valor distinto se ignora y se borra (RF-003).

## Decisiones
### D-01 CSS plano por componente con las clases de la referencia
Elegida: un archivo `.css` junto a cada componente, importado por él, con los nombres de clase y las medidas de `docs/referencia/*.html`.
Descartada: CSS Modules, Tailwind o CSS en JavaScript.
Motivo: la referencia ya es CSS plano; copiar sus reglas evita retraducirlas, y los nombres de clase estables permiten comparar y depurar contra ella. No añade dependencias.

### D-02 Tokens con los nombres de la referencia y tema por atributo
Elegida: `tokens.css` v2 con las variables de la referencia; claro por defecto, oscuro con `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` y `:root[data-theme="dark"]`.
Descartada: conservar los nombres `--color-*` de Niebla marina y mapearlos.
Motivo: el CSS de la referencia se reutiliza sin cambios; el test de tokens se reescribe contra las tablas de la guía.

### D-03 Tema en un módulo propio con almacenamiento inyectable
Elegida: `theme/theme.ts` (leer, validar, aplicar, alternar), aplicado en `main.tsx` antes de renderizar.
Descartada: un contexto de React que lo aplique tras el primer render.
Motivo: evita el parpadeo del tema equivocado y sigue el patrón probado de `i18n/language.ts`. Sustituye a D-13 de `registro-flujo` («sin selector de tema»); esa decisión no se edita aquí.

### D-04 Iconos con `lucide-react` por importación nominal
Elegida: `lucide-react`, importando cada icono por su nombre.
Descartada: copiar los SVG de las referencias al código.
Motivo: lo pediste; mantiene los iconos al día y el empaquetado solo incluye los usados. Las formas de alarma no están en la librería y son propias (M-03).

### D-05 Menú desplegable propio, patrón «select-only combobox»
Elegida: un único menú compartido (M-04) con el patrón de combobox de solo selección de WAI-ARIA, sin librería.
Descartada: usar una librería de componentes accesibles.
Motivo: no se añaden dependencias y tres piezas (selector, idioma, pestañas) comparten comportamiento y animación.

### D-06 El disparador del selector es un `<button role="combobox" name value>`
Elegida: botón con `name` y `value`, `role="combobox"` y `aria-activedescendant`.
Descartada: un `<input type="hidden">` más un botón sin nombre.
Motivo: `useFormValidation` lee el valor con `form.elements.namedItem(name).value` y enfoca ese mismo elemento; un botón con `name` cumple ambas cosas y conserva `onBlur`.

### D-07 Selector táctil con `matchMedia("(pointer: coarse)")`
Elegida: un hook decide en cada render si usar el `<select>` nativo (puntero principal táctil) o el propio.
Descartada: detectar por el agente del navegador o por el ancho de pantalla.
Motivo: el tipo de puntero es lo que RF-031 describe; el ancho no distingue una tablet de una ventana estrecha.

### D-08 Estilo por consultas de medios en CSS; comportamiento por `useMediaQuery`
Elegida: CSS decide el aspecto en 1100, 768 y 560 px; `useMediaQuery` solo decide lo que cambia el comportamiento (foco, `aria-hidden`, cierre del panel).
Descartada: resolver todo en JavaScript.
Motivo: el aspecto no depende de que React haya medido; la lógica solo se ejecuta donde hace falta.

### D-09 Pestañas: línea y desbordamiento medidos con `ResizeObserver`
Elegida: medir las pestañas para posicionar la línea y para decidir cuándo pasar al selector.
Descartada: CSS puro con `:has()` y variables.
Motivo: la línea debe animarse entre posiciones y el desbordamiento depende del texto traducido. jsdom no calcula layout: los tests unitarios simulan las medidas y la verificación real la hace el test visual (M-12).

### D-10 Gráfica SVG generada por React con escala en una función pura
Elegida: `chartScale.ts` calcula eje (múltiplos de 30), ancho de grupo y posiciones; `BarChart` solo las dibuja.
Descartada: una librería de gráficas.
Motivo: lo definiste (gráficas propias en SVG) y la escala se prueba sin navegador.

### D-11 Test visual con Playwright, ejecutado con Vitest en un proyecto aparte
Elegida: `playwright` como dependencia de desarrollo, ejecutado por Vitest con su propia configuración (`test:visual`, entorno node) y un trabajo de CI separado que instala Chromium.
Descartada: `@playwright/test` como segundo ejecutor de tests.
Motivo: un solo ejecutor y reutiliza el script `comparar.cjs`. El test visual queda fuera del umbral de cobertura. Añadir `playwright` y la descarga de Chromium exige tu permiso expreso antes de instalarlo (AGENTS.md, «No añadir dependencias nuevas»).

### D-12 `base.css` deja de estilar elementos sueltos
Elegida: cada componente trae sus clases; `base.css` solo tiene reinicio, fuente, foco y movimiento reducido.
Descartada: mantener selectores como `button`, `input` y `section` y sobrescribirlos.
Motivo: esos selectores filtrarían estilos a las piezas nuevas y rompen la igualdad exacta con la referencia (RF-028).

### D-13 Textos nuevos en los tres idiomas, con paridad exigida por los tests existentes
Elegida: claves nuevas en `es`, `pt-BR` y `en`; `keys.test.ts` y `locales.test.ts` ya fallan si falta alguna.
Descartada: textos en un solo idioma hasta tener las traducciones.
Motivo: RF-030 y el criterio de `componentes-base-accesibles`; añadirlos después obliga a rehacer.

## Estrategia de tests
- **Unitario (Vitest + Testing Library + user-event):** cada pieza prueba su comportamiento (teclado, `aria-*`, estados vacíos, anuncios) y pasa `axe-core` en jsdom. Los tests existentes de botón, campos, mensajes, selector de idioma y registro se conservan; solo `ChoiceFields.test.tsx` se reescribe por el selector propio (RF-016, RF-031).
- **Tokens y tema:** `tokens.test.ts` compara las variables con las tablas de la guía en ambos temas; `theme.test.ts` cubre RF-001 a RF-003 con almacenamiento simulado.
- **Escala de la gráfica:** función pura con casos límite (valores mayores de 120, un solo grupo, negativos, vacío).
- **Visual (Playwright, `test:visual`):** igualdad exacta de las propiedades de RF-028 entre el catálogo y las dos referencias en claro y oscuro; contraste AA con `axe-core` en ambos temas (RF-029); comprobación real de la línea de pestañas y del desbordamiento.
- **Cobertura:** Vitest con umbral de líneas ≥ 80 % (P-05); el test visual queda fuera.
- **Comandos de calidad:** `pnpm --filter frontend test`, `typecheck`, `lint`, `format --check` y `test:visual`.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02 | unitario (tema), visual |
| RF-002 | M-02 | unitario |
| RF-003 | M-02 | unitario |
| RF-004 | M-01 | unitario (lee la regla de movimiento reducido), visual |
| RF-005 | M-05, M-10 | unitario, visual |
| RF-006 | M-05 | unitario, visual |
| RF-007 | M-05, M-10 | unitario, visual |
| RF-008 | M-05 | unitario, visual |
| RF-009 | M-05 | unitario, visual |
| RF-010 | M-06 | unitario, visual |
| RF-011 | M-04, M-06 | unitario, visual |
| RF-012 | M-06 | unitario, visual |
| RF-013 | M-06 | unitario, visual |
| RF-014 | M-07 | unitario, visual |
| RF-015 | M-08 | unitario, visual |
| RF-016 | M-04, M-08 | unitario (teclado y `aria-*`), visual |
| RF-017 | M-08 | unitario, visual |
| RF-018 | M-07 | unitario, visual |
| RF-019 | M-07 | unitario, visual |
| RF-020 | M-03, M-07 | unitario, visual |
| RF-021 | M-09 | unitario, visual |
| RF-022 | M-09 | unitario, visual |
| RF-023 | M-07 | unitario, visual |
| RF-024 | M-09 | unitario (escala), visual |
| RF-025 | M-03, M-09 | unitario, visual |
| RF-026 | M-11 | unitario (tests previos), visual |
| RF-027 | M-11 | unitario, visual |
| RF-028 | M-12 | visual |
| RF-029 | M-01, M-12 | unitario (axe), visual (contraste) |
| RF-030 | M-10 | unitario (paridad de claves) |
| RF-031 | M-08 | unitario |

## RF sin cobertura
Ninguno.
