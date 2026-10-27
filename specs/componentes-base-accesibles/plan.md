# Plan: componentes-base-accesibles
Estado: aprobado

Base de código: `frontend/` tal como está en `main` (React 18, Vite, Vitest con jsdom, Testing
Library, TypeScript estricto). Solo se toca `frontend/`: ni el backend ni `desktop/` cambian (S-07).

## Dependencias nuevas
- `i18next` y `react-i18next` (ejecución): autorizadas por el usuario (D-01).
- `@testing-library/user-event` (desarrollo): autorizada por el usuario (D-12).
- `axe-core` (desarrollo): autorizada por el usuario (D-13).

El contenedor `frontend` de Docker ya ejecuta `pnpm install` al arrancar, así que las dependencias
nuevas no añaden pasos manuales (P-02).

## Módulos
### M-01 Instancia de traducción (`src/i18n/index.ts`, `src/i18n/i18next.d.ts`)
Responsabilidad: `createI18n(language)` crea y arranca una instancia de i18next con los tres
idiomas incluidos en el código (D-03), `fallbackLng: "en"` y sin devolver textos vacíos ni nulos
(RF-007), e inicialización síncrona para que el primer pintado ya salga traducido. `main.tsx` crea
la instancia con el idioma de M-03 y la pasa a la app con el proveedor de `react-i18next`; los tests
crean una propia en cada caso. `i18next.d.ts` declara los recursos con el tipo de `en` para que
`t()` con una clave inexistente sea un error de tipos (D-04).
RF: RF-001, RF-007, RF-008

### M-02 Textos (`src/i18n/locales/en.ts`, `src/i18n/locales/es.ts`, `src/i18n/locales/pt-BR.ts`)
Responsabilidad: los textos provisionales de los tres idiomas (S-01), como objetos TypeScript.
`en.ts` define la forma; `es.ts` y `pt-BR.ts` se declaran con ese tipo, de modo que una clave que
falte o sobre no compila (D-04). Grupos de claves: `app` (título del documento), `language`
(etiqueta del selector), `button` (procesando), `field` (leyenda del asterisco, mostrar
contraseña), `message` (prefijos «Error:», «Éxito:», «Información:»), `validation` (vacío, correo,
código incompleto, demasiados intentos, error del servidor) y `showcase` (etiquetas, botones y
mensajes de la página de muestra). Los nombres de los idiomas del selector no se traducen: cada uno
va siempre en su propio idioma (RF-003).
RF: RF-001, RF-008

### M-03 Idioma del usuario (`src/i18n/language.ts`)
Responsabilidad: funciones puras y sin estado global:
- `SUPPORTED_LANGUAGES = ["es", "pt-BR", "en"]` y `LANGUAGE_NAMES` (nombre de cada uno en su idioma).
- `matchLanguage(tag)`: `es-*` → `es`, `pt-*` → `pt-BR`, `en-*` → `en`, sin distinguir mayúsculas;
  cualquier otro → ninguno.
- `detectInitialLanguage(navigatorLanguages, storage)`: el idioma guardado si es válido; si está
  guardado y no es válido, lo borra (RF-023); si no hay uno válido, el primer idioma del navegador
  que encaje con `matchLanguage`; si ninguno encaja, `en` (RF-002).
- `persistLanguage(language, storage)`: lo guarda con la clave `confiabilidad.language`.
Todo acceso al almacenamiento va protegido: si el navegador lo bloquea o lanza un error, la
función se comporta como si no hubiera nada guardado (S-04).
RF: RF-002, RF-005, RF-023

### M-04 Selector de idioma y documento (`src/components/LanguageSwitcher.tsx`, `src/i18n/useDocumentLanguage.ts`)
Responsabilidad: `LanguageSwitcher` es un grupo con nombre accesible traducido («Idioma») y un
botón por idioma (D-06). Cada botón muestra el nombre del idioma con su atributo `lang`, marca el
activo con `aria-pressed="true"` y, al activarse, cambia el idioma de la instancia y lo guarda
(M-03). Los botones conservan su identidad entre renderizados, así que el foco no se mueve
(RF-004). `useDocumentLanguage` mantiene `<html lang>` y `document.title` sincronizados con el idioma
activo, al arrancar y en cada cambio (RF-004, RF-006).
RF: RF-003, RF-004, RF-005, RF-006

### M-05 Anunciador (`src/components/LiveAnnouncer.tsx`)
Responsabilidad: un proveedor que monta, desde el primer renderizado, dos regiones vivas
invisibles a la vista, una educada (`polite`) y otra urgente (`assertive`), y expone
`announce(text, politeness)` con el hook `useAnnouncer`. Vacía la región y escribe el texto en el
siguiente ciclo, para que los lectores lo anuncien aunque se repita el mismo texto (D-08).
RF: RF-010, RF-017

### M-06 Botón (`src/components/Button.tsx`)
Responsabilidad: un `<button>` nativo (Enter y Espacio sin código propio, RF-009) cuyo texto es su
nombre accesible. Con `processing`: muestra el texto traducido «Procesando…», marca
`aria-disabled="true"` en lugar de `disabled` para no salir del orden de tabulación ni perder el
foco (D-07), cancela el clic (y con él el envío implícito con Enter desde un campo) y, al entrar en
ese estado, anuncia «procesando» en la región educada de M-05. Al salir no anuncia nada (RF-010).
RF: RF-009, RF-010

### M-07 Campos de texto (`src/components/fields/TextField.tsx`, `src/components/fields/PasswordField.tsx`, `src/components/fields/RequiredLegend.tsx`)
Responsabilidad:
- `TextField` (tipos `text` y `email`): `<label>` asociado por `id` (con `useId`), marca visible
  `*` oculta al lector y `aria-required="true"` cuando es obligatorio (D-09), `autocomplete` e
  `inputmode` según el tipo (`email` → `autocomplete="email"`, `inputmode="email"`; `text` → el que
  indique la pantalla) y el error de campo (RF-016): el mensaje en un elemento con `id` propio,
  `aria-invalid="true"` y `aria-describedby` apuntando a él; sin error no queda ninguno de los tres.
- `PasswordField`: se apoya en `TextField`; la prop `kind: "current" | "new"` es obligatoria en el
  tipo, así que no compila un uso sin ella (RF-024), y fija
  `autocomplete="current-password" | "new-password"`. El control de mostrar u ocultar es un
  `<button type="button">` con nombre fijo («Mostrar contraseña») y `aria-pressed` (D-10); al
  activarse alterna el `type` del input entre `password` y `text` sin desmontarlo, así que conserva
  el valor y el foco se queda en el control (RF-012).
- `RequiredLegend`: el texto visible que explica el asterisco (RF-011).
RF: RF-011, RF-012, RF-016, RF-024

### M-08 Campo del código (`src/components/fields/CodeField.tsx`, `src/components/fields/code.ts`)
Responsabilidad: `code.ts` con dos funciones puras: `normalizeTypedCode(value)` convierte los
dígitos de ancho completo y arábigos a `0`-`9`, descarta el resto y recorta a 6 (RF-013); y
`extractPastedCode(text)` devuelve los 6 primeros dígitos (convertidos) del texto, o nada si no
tiene ninguno (RF-014). `CodeField` es un único input con la estructura de etiqueta, obligatoriedad
y error de `TextField`, `inputmode="numeric"`, `autocomplete="one-time-code"` y sin `maxlength`
nativo (el recorte lo hace `normalizeTypedCode`, que también cubre los dígitos convertidos). En el
evento de pegar, cancela el pegado por defecto y sustituye el valor por `extractPastedCode`, salvo
que no haya dígitos (RF-014). No envía ni mueve el foco al llegar a 6 dígitos (RF-015).
RF: RF-013, RF-014, RF-015, RF-016

### M-09 Mensaje general (`src/components/FormMessage.tsx`)
Responsabilidad: muestra un mensaje de tipo `error`, `success` o `info` con un prefijo visible y
traducido («Error:», «Éxito:», «Información:») que dice al lector su tipo (D-11). Recibe la clave de
traducción, no el texto, y lo traduce al pintar (RF-018). Expone `focus()` con un `ref` sobre un
contenedor con `tabIndex={-1}` (enfocable por código, fuera del orden de tabulación).
RF: RF-017, RF-018

### M-10 Estado y validación del formulario (`src/forms/useFormValidation.ts`)
Responsabilidad: un hook que recibe los campos en orden visual, cada uno con sus validadores
locales (devuelven una clave de error o nada), y gestiona:
- los errores locales: al salir de un campo, desde el principio, valida ese campo y pone o quita su
  error; al enviar, valida todos (RF-025);
- los errores de servidor por campo y el mensaje general: los fija la pantalla tras enviar, y se
  conservan hasta el siguiente envío; la validación al salir no los toca (RF-025, RF-017). Si un
  campo tiene a la vez error local y de servidor, se muestra el local (D-14);
- el foco tras enviar: al primer campo con error en orden visual; si no hay ninguno y hay mensaje
  general, al mensaje; si hay ambos, foco al campo y anuncio del mensaje general por M-05, urgente si
  es un error y educado si no (RF-017, RF-021);
- `processing`: mientras está activo, un segundo envío se ignora (refuerzo de RF-010).
Los errores se guardan como claves de traducción con sus parámetros, nunca como texto, así que un
cambio de idioma los repinta traducidos sin perder el estado (D-05, RF-018).
RF: RF-016, RF-017, RF-018, RF-021, RF-025

### M-11 Página de muestra (`src/showcase/ShowcasePage.tsx`, `src/showcase/validators.ts`, `src/App.tsx`)
Responsabilidad: `App` monta el proveedor de M-05, `useDocumentLanguage` y `ShowcasePage`, que
sustituye al contenido actual (S-06). La página tiene un título, el selector de idioma (M-04), la
leyenda del asterisco y un formulario `noValidate` con, en este orden: un campo de texto, uno de
correo, uno de contraseña actual (S-09), el campo del código, el botón de envío y un botón
«Mostrar error general de ejemplo». `validators.ts` define las reglas de RF-021: obligatorio
(vacío o solo espacios), correo (`^[^@\s]+@[^@\s]+$`: una sola `@`, algo antes y después, sin
espacios) y código de 6 dígitos. Un envío válido pone el botón en «procesando» 3 segundos y después
muestra el mensaje informativo de demostración (RF-022). El botón de ejemplo fija un error general
de «demasiados intentos» y le lleva el foco.
RF: RF-019, RF-020, RF-021, RF-022

## Modelo de datos
No hay datos de servidor ni cambios de backend. El único dato persistente es el idioma elegido, en
el almacenamiento local del navegador con la clave `confiabilidad.language` y uno de los valores
`es`, `pt-BR` o `en` (M-03). Los textos viven en M-02 con la forma `{ grupo: { clave: texto } }` y
parámetros de interpolación de i18next (`{{count}}`) donde hagan falta.

## Decisiones
### D-01 Librería de traducción
Elegida: `i18next` + `react-i18next`.
Descartada: un diccionario propio con un hook de React.
Motivo: decisión del usuario. Aporta interpolación, plurales por idioma, idioma de reserva y
repintado al cambiar de idioma ya probados, que las pantallas reales van a necesitar.

### D-02 Detección del idioma propia
Elegida: las funciones de M-03 (unas decenas de líneas).
Descartada: `i18next-browser-languagedetector`.
Motivo: sus reglas no coinciden con la spec: no asigna `pt-PT` a `pt-BR`, no borra un valor
guardado no válido (RF-023) y su orden de fuentes (cookie, querystring…) añade comportamientos que
la spec no pide. Además sería otra dependencia.

### D-03 Textos incluidos en el código
Elegida: los tres idiomas como módulos importados al arrancar.
Descartada: cargarlos por HTTP con `i18next-http-backend`.
Motivo: son unos pocos kilobytes; cargarlos aparte mostraría claves o huecos durante la carga,
añadiría una dependencia y fallaría sin red en la app de escritorio.

### D-04 Claves comprobadas por el compilador
Elegida: textos en TypeScript con `es` y `pt-BR` tipados como `en`, y los recursos declarados para
`react-i18next` con ese tipo. Una clave que falte, sobre o no exista en `t()` rompe `tsc`.
Complementa un test que recorre los tres idiomas y falla con claves distintas o textos vacíos, y un
uso de `t()` con clave inexistente marcado `@ts-expect-error` que prueba que la comprobación de
tipos sigue activa (RF-008).
Descartada: archivos JSON.
Motivo: un JSON importado no tiene la comprobación de propiedades sobrantes ni se puede tipar
contra otro idioma, así que las claves que sobran o faltan solo se verían en ejecución.

### D-05 Errores como claves, no como textos
Elegida: el estado de errores y mensajes guarda la clave y sus parámetros; se traduce al pintar.
Descartada: guardar el texto ya traducido.
Motivo: con el texto guardado, cambiar de idioma dejaría los errores en el idioma anterior hasta el
siguiente envío (RF-018).

### D-06 Selector de idioma como grupo de botones
Elegida: un grupo con nombre accesible y un botón por idioma con `aria-pressed`.
Descartada: un `<select>` nativo o un grupo de radios.
Motivo: en los dos descartados, moverse con las flechas cambia el valor y, con él, el idioma de
toda la página a cada pulsación, un cambio de contexto inesperado (WCAG 3.2.2). Con botones, el
idioma solo cambia al activar uno con Enter, Espacio o clic, y el atributo `lang` del nombre de
cada idioma se aplica a un texto normal, que los lectores respetan mejor que dentro de un `<option>`.

### D-07 «Procesando» con `aria-disabled`
Elegida: `aria-disabled="true"` y cancelar el clic mientras procesa.
Descartada: el atributo `disabled`.
Motivo: `disabled` saca el botón del orden de tabulación y, si tenía el foco, el foco se pierde al
`<body>`, lo que incumple RF-010.

### D-08 Anuncios con regiones vivas permanentes
Elegida: dos regiones vivas montadas desde el arranque (M-05), donde se escribe el texto que hay
que anunciar.
Descartada: crear un elemento con `role="status"` o `role="alert"` en el momento del anuncio.
Motivo: muchos lectores no anuncian una región viva que aparece ya con texto; solo anuncian los
cambios de una región que ya existía.

### D-09 Obligatoriedad con `aria-required`
Elegida: `aria-required="true"` y un `*` visible con `aria-hidden="true"`.
Descartada: el atributo `required` nativo.
Motivo: el nativo activa las burbujas de validación del navegador, en su idioma y no en el de la
interfaz, y compite con RF-021 y RF-025. Ocultar el asterisco al lector evita que lea «asterisco»
además de «obligatorio».

### D-10 Mostrar contraseña como botón conmutador
Elegida: nombre fijo «Mostrar contraseña» con `aria-pressed` verdadero o falso.
Descartada: cambiar el nombre entre «Mostrar» y «Ocultar».
Motivo: un nombre que cambia sobre el elemento enfocado no se anuncia de forma fiable (el mismo
problema que en C-05); `aria-pressed` sí se anuncia al cambiar («presionado» / «no presionado»).

### D-11 Tipo del mensaje general con prefijo visible
Elegida: un prefijo de texto visible y traducido («Error:», «Éxito:», «Información:»).
Descartada: distinguirlo solo con `role="alert"` frente a `role="status"`.
Motivo: el mensaje recibe el foco y el lector lee su texto, no su rol; el prefijo se lee igual en
todos los lectores, lo ve también quien no usa lector y no depende del color, que aún no existe.

### D-12 Teclado simulado en los tests
Elegida: `@testing-library/user-event` (dependencia de desarrollo).
Descartada: `fireEvent` de Testing Library, que ya está instalado.
Motivo: `fireEvent` no mueve el foco con Tab, no convierte Espacio o Enter en un clic de botón, no
hace el envío implícito de un formulario con Enter y no simula el portapapeles. Sin él, RF-009,
RF-010, RF-014, RF-015, RF-019 y RF-021 solo se podrían probar de forma parcial.

### D-13 Auditoría automática de accesibilidad en los tests
Elegida: `axe-core` (dependencia de desarrollo), ejecutado sobre la página de muestra en sus
estados principales (inicial, con errores, procesando, con mensaje general) y en los tres idiomas.
Descartada: no auditar, o usar `jest-axe` o `vitest-axe`.
Motivo: detecta etiquetas que faltan, `id` repetidos, ARIA mal usado y `lang` no válidos que los
tests escritos a mano pueden no cubrir. Se usa `axe-core` directamente porque `vitest-axe` está
abandonado (0.1.0) y `jest-axe` está pensado para Jest.

### D-14 Error local por delante del de servidor
Elegida: si un campo tiene a la vez un error local y uno de servidor, se muestra el local.
Descartada: mostrar el de servidor o los dos.
Motivo: un error local nuevo describe el valor actual (el usuario lo ha cambiado tras enviar),
mientras que el de servidor describe el valor ya enviado; mostrar los dos duplica el anuncio al
llegar al campo.

### D-15 Contraseña fuera de correctores y autocorrección
Elegida: el input de `PasswordField` lleva siempre `spellcheck="false"`, `autocapitalize="off"` y
`autocorrect="off"`.
Descartada: dejar el comportamiento por defecto del navegador.
Motivo: al mostrar la contraseña (RF-012), el input pasa a `type="text"`; con la revisión
ortográfica mejorada de Chrome o extensiones de corrección, el texto visible puede enviarse a
servidores externos, y en móvil el teclado puede autocorregirlo o capitalizarlo. Decisión de
seguridad tomada por el usuario durante E-04.

## Estrategia de tests
Todo con Vitest en jsdom (`pnpm --filter frontend test`), con cobertura de líneas ≥ 80 % (P-05),
TDD estricto (P-04) y un mutante por tarea (`sdd-implementar`).
- **Unitario** (funciones puras, sin DOM): M-03 (asignación de variantes, orden de preferencia,
  inglés cuando ninguno encaja, valor guardado no válido borrado, almacenamiento que lanza errores),
  M-08 `code.ts` (conversión de dígitos, descarte, recorte, pegado sin dígitos) y M-11
  `validators.ts`. Cubre RF-002, RF-005, RF-013, RF-014, RF-021 y RF-023.
- **Traducciones**: un test que compara las claves de los tres idiomas y busca textos vacíos, y un
  test que fuerza una clave ausente en `es` para ver el texto inglés (RF-007, RF-008). `tsc` en la
  suite de CI con el `@ts-expect-error` de D-04.
- **Componente** (Testing Library + `user-event`): cada componente en aislamiento, consultando por
  rol y nombre accesible (lo que expone el árbol de accesibilidad), con asserts sobre `aria-*`,
  `lang`, `autocomplete`, `inputmode`, foco (`toHaveFocus`) y el texto de las regiones vivas de
  M-05. Cubre RF-003, RF-004, RF-006, RF-009 a RF-018 y RF-024.
- **Integración** (página de muestra completa): orden de tabulación de principio a fin, envío con
  errores y foco, envío válido con temporizadores simulados (3 s), error general de ejemplo, cambio
  de idioma conservando valores, errores, foco, `lang` y título, y la auditoría de `axe-core`
  (D-13). Cubre RF-001, RF-004, RF-018 a RF-022 y RF-025.
- **Manual** (fuera de la suite): el recorrido solo con teclado (CF-3) y el checklist de lector de
  pantalla con NVDA o VoiceOver (CF-5, S-08), que va en `resumen.md` y en `HUMAN_TODO.md`. jsdom no
  pronuncia ni aplica `inputmode` o `autocomplete`: los tests prueban que los atributos están; el
  efecto real lo confirma la prueba manual.

## Trazabilidad
| RF | Módulo(s) | Nivel de test |
|---|---|---|
| RF-001 | M-01, M-02 | Traducciones, integración |
| RF-002 | M-03 | Unitario |
| RF-003 | M-04 | Componente |
| RF-004 | M-04, M-01 | Componente, integración |
| RF-005 | M-03, M-04 | Unitario, componente |
| RF-006 | M-04 | Componente, manual |
| RF-007 | M-01 | Traducciones |
| RF-008 | M-01, M-02 | Traducciones, `tsc` |
| RF-009 | M-06 | Componente |
| RF-010 | M-06, M-05, M-10 | Componente, integración |
| RF-011 | M-07 | Componente |
| RF-012 | M-07 | Componente |
| RF-013 | M-08 | Unitario, componente, manual |
| RF-014 | M-08 | Unitario, componente |
| RF-015 | M-08 | Componente |
| RF-016 | M-07, M-08, M-10 | Componente |
| RF-017 | M-09, M-10, M-05 | Componente, integración |
| RF-018 | M-09, M-10 | Componente, integración |
| RF-019 | M-04, M-06, M-07, M-08, M-11 | Integración, manual |
| RF-020 | M-11 | Integración, manual |
| RF-021 | M-11, M-10 | Unitario, integración |
| RF-022 | M-11 | Integración |
| RF-023 | M-03 | Unitario |
| RF-024 | M-07 | Componente, `tsc` |
| RF-025 | M-10 | Componente, integración |

## RF sin cobertura
Ninguno.
