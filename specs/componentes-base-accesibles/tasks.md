# Tareas: componentes-base-accesibles
Estado: aprobado

Rutas relativas a `frontend/src/` salvo que se indique. Los tests van junto al archivo que prueban
(`X.test.ts` o `X.test.tsx`). "Suite verde" = `pnpm --filter frontend test`,
`pnpm --filter frontend typecheck`, `pnpm --filter frontend lint` y
`pnpm --filter frontend exec prettier --check .` sin errores ni avisos, con cobertura de líneas
≥ 80 % (`pnpm --filter frontend test:coverage`). En cada tarea, antes de marcarla, se prueba al
menos un mutante del código que introduce y debe hacer fallar sus tests.

Los textos de toda la feature se escriben en T-001 para que ninguna tarea posterior tenga que tocar
los tres archivos de idioma a la vez.

- [x] T-001 Textos provisionales de toda la feature en tres idiomas
  RF: RF-001, RF-008 (D-04) | Depende de: — | Archivos: 4
  Archivos: `i18n/locales/en.ts`, `i18n/locales/es.ts`, `i18n/locales/pt-BR.ts`,
  `i18n/locales/locales.test.ts`.
  Hecho cuando: los tres idiomas tienen los grupos de M-02 (`app`, `language`, `button`, `field`,
  `message`, `validation`, `showcase`) con textos de cuenta de usuario de una herramienta de
  gestión de activos industriales (S-01); `es` y `pt-BR` están tipados con la forma de `en`; el
  test falla si un idioma tiene una clave de más o de menos o un texto vacío (comprobado quitando
  una clave y vaciando un texto); suite verde.
  Excepción: los tres archivos de idioma son una sola unidad: `es` y `pt-BR` se tipan contra `en`,
  así que separarlos dejaría `tsc` roto entre tareas.
  Decisiones: además de los grupos de M-02, se añaden `button.processingAnnouncement` (el aviso
  «procesando» sin puntos suspensivos, distinto del texto visible) y `showcase.formTitle` (nombre
  accesible del formulario de ejemplo) — [Probable] — revertir: borrar las dos claves de los tres
  idiomas. El nombre de la app se traduce («Confiabilidad», «Confiabilidade», «Reliability») porque
  C-12 pide traducir el título — [Suposición] — revertir: usar «Confiabilidad» en los tres.

- [x] T-002 Instancia de traducción con reserva en inglés
  RF: RF-001, RF-007 (D-01, D-03) | Depende de: T-001 | Archivos: 4
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `i18n/index.ts`, `i18n/index.test.ts`.
  Hecho cuando: `i18next` y `react-i18next` están en `dependencies`; `createI18n("pt-BR")`
  devuelve una instancia ya inicializada que traduce una clave al portugués en el primer acceso
  (sin esperar promesas); una clave ausente en `es` (recurso de prueba) devuelve el texto inglés y
  nunca la clave; suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`; no es un archivo editado a mano.
  Decisiones: `createI18n` acepta los textos como segundo parámetro (por defecto, los tres de M-02)
  para probar la reserva con un recurso incompleto sin tocar los reales — [Cierto] — revertir:
  quitar el parámetro y probar con `addResourceBundle`. Un texto vacío también cae al inglés
  (`returnEmptyString: false`) — [Cierto] — revertir: quitar la opción. Mutante equivalente: con
  los textos incluidos, `initAsync: true` también traduce en el primer acceso en i18next 26; se
  mantiene `initAsync: false` explícito para no depender de ese detalle — [Probable] — revertir:
  quitar la opción.

- [x] T-003 Claves de traducción comprobadas por el compilador
  RF: RF-008 (D-04) | Depende de: T-002 | Archivos: 2
  Archivos: `i18n/i18next.d.ts`, `i18n/keys.test.ts`.
  Hecho cuando: `keys.test.ts` contiene un `t("clave.que.no.existe")` marcado con
  `@ts-expect-error` y `pnpm --filter frontend typecheck` pasa; al borrar `i18next.d.ts`,
  `typecheck` falla por esa directiva sin uso; suite verde.
  Decisiones: la declaración fija también `returnNull: false`, para que `t()` devuelva siempre
  `string` y los componentes no tengan que tratar `null` — [Cierto] — revertir: quitar la línea.
  La comprobación la hace `tsc` (`pnpm --filter frontend typecheck`, que corre en CI), no Vitest,
  que no comprueba tipos — [Cierto] — revertir: no aplica.

- [x] T-004 Idioma inicial según el navegador
  RF: RF-002 | Depende de: — | Archivos: 2
  Archivos: `i18n/language.ts`, `i18n/language.test.ts`.
  Hecho cuando: `matchLanguage` asigna `es-MX` → `es`, `PT-pt` → `pt-BR`, `en-GB` → `en` y `fr` →
  ninguno; `detectInitialLanguage(["fr-FR", "pt-PT", "en"], almacenamiento vacío)` devuelve
  `pt-BR`; con `["fr-FR", "de"]` o con una lista vacía devuelve `en`; suite verde.
  Decisiones: en esta tarea `detectInitialLanguage` recibe solo los idiomas del navegador; el
  parámetro del almacenamiento llega con T-007, que es quien lo usa (añadirlo antes dejaría un
  parámetro sin uso, que `tsc` rechaza) — [Cierto] — revertir: no aplica. La correspondencia usa un
  `Map` para que etiquetas como `constructor` no encajen con propiedades heredadas de `Object` —
  [Cierto] — revertir: volver a un objeto literal. `LANGUAGE_NAMES` se define aquí (M-03) aunque
  lo use T-008 — [Cierto] — revertir: moverlo al selector.

- [x] T-005 Idioma y título del documento sincronizados
  RF: RF-004, RF-006 | Depende de: T-002 | Archivos: 2
  Archivos: `i18n/useDocumentLanguage.ts`, `i18n/useDocumentLanguage.test.tsx`.
  Hecho cuando: al montar con la instancia en `pt-BR`, `<html lang>` es `pt-BR` y `document.title`
  es el título portugués; tras `changeLanguage("en")` ambos pasan a inglés sin volver a montar;
  suite verde.

- [x] T-006 Aplicación traducida al arrancar
  RF: RF-001, RF-002 | Depende de: T-003, T-004, T-005 | Archivos: 3
  Archivos: `App.tsx`, `App.test.tsx`, `main.tsx`.
  Hecho cuando: `main.tsx` crea la instancia con `detectInitialLanguage(navigator.languages, …)` y
  la pasa con el proveedor de `react-i18next`; `App` usa `useDocumentLanguage` y muestra el título
  y la introducción de `app` traducidos; el test renderiza `App` en `es`, `pt-BR` y `en` y
  encuentra el encabezado por rol y nombre en cada idioma; suite verde.
  Decisiones: `main.tsx` no tiene test unitario (está excluido de la cobertura); su arranque se
  comprobó en Chromium con los idiomas de navegador `pt-BR`, `en-US`, `fr-FR` y `es-AR` — [Cierto]
  — revertir: no aplica. `index.html` sigue con `lang="es"` hasta que arranca la app, que lo
  sustituye; cambiarlo queda fuera de los archivos de la tarea — [Probable] — revertir: no aplica.

- [x] T-007 Idioma elegido guardado en el navegador
  RF: RF-005, RF-023 (S-04) | Depende de: T-004 | Archivos: 2
  Archivos: `i18n/language.ts`, `i18n/language.test.ts`.
  Hecho cuando: `persistLanguage("pt-BR", almacenamiento)` guarda el valor en
  `confiabilidad.language`; `detectInitialLanguage` prefiere un valor guardado válido al del
  navegador; con un valor guardado `fr` lo borra y aplica RF-002; con un almacenamiento cuyo
  `getItem`, `setItem` o `removeItem` lanzan errores no lanza nada y aplica RF-002; suite verde.
  Decisiones: el almacenamiento es un parámetro opcional de `detectInitialLanguage`, así que las
  llamadas de T-004 sin él siguen valiendo — [Cierto] — revertir: hacerlo obligatorio. Se añade
  `browserStorage()`, que devuelve `window.localStorage` o nada si el navegador bloquea el acceso
  (que también puede lanzar), para que T-009 lo use en `main.tsx` — [Cierto] — revertir: mover esa
  protección a `main.tsx`. Un valor guardado solo vale si es exactamente `es`, `pt-BR` o `en`
  (`pt` guardado se borra) — [Probable] — revertir: pasar el valor por `matchLanguage`.

- [x] T-008 Selector de idioma
  RF: RF-003, RF-004, RF-005, RF-006 (D-06) | Depende de: T-002, T-007 | Archivos: 4
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `components/LanguageSwitcher.tsx`,
  `components/LanguageSwitcher.test.tsx`.
  Hecho cuando: `@testing-library/user-event` está en `devDependencies`; el selector es un grupo
  con nombre accesible traducido y tres botones «Español», «Português (Brasil)» y «English», cada
  uno con su `lang` y con `aria-pressed="true"` solo en el activo; con `user-event`, Tab hasta
  «English» y Enter (y, en otro caso, Espacio) cambia el idioma de la instancia, lo guarda con
  `persistLanguage`, marca el botón como activo y deja el foco en él; suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`; no es un archivo editado a mano.
  Decisiones: el selector recibe el almacenamiento como prop opcional (sin él, cambia el idioma
  pero no lo guarda), para probarlo con uno en memoria — [Cierto] — revertir: leer
  `browserStorage()` dentro del componente. El grupo usa `role="group"` con `aria-label` en lugar
  de `<fieldset>`, que no es un formulario — [Probable] — revertir: `<fieldset>` y `<legend>`. Los
  botones son `type="button"` para no enviar un formulario que los contenga — [Cierto] — revertir:
  quitar el atributo.

- [x] T-009 Selector de idioma en la aplicación
  RF: RF-004, RF-005 | Depende de: T-006, T-008 | Archivos: 3
  Archivos: `App.tsx`, `App.test.tsx`, `main.tsx`.
  Hecho cuando: `main.tsx` pasa `window.localStorage` (protegido) a `detectInitialLanguage`; `App`
  muestra el selector; el test cambia de `es` a `pt-BR` con el teclado y comprueba el encabezado
  portugués, `<html lang="pt-BR">`, el título portugués y el foco en el botón; suite verde.
  Decisiones: `main.tsx` obtiene el almacenamiento con `browserStorage()` (T-007) y `App` lo recibe
  como prop para pasarlo al selector — [Cierto] — revertir: leerlo dentro del selector. El selector
  va antes del encabezado, primero en el orden de tabulación — [Probable] — revertir: moverlo
  detrás. Comprobado en Chromium: con el navegador en francés sale en inglés; Tab, Tab, Enter pasa
  a portugués con el foco en «Português (Brasil)»; al recargar sigue en portugués; un valor
  guardado `xx` se borra y vuelve al idioma del navegador — [Cierto] — revertir: no aplica.

- [x] T-010 Campo de texto y de correo
  RF: RF-011, RF-016 (D-09) | Depende de: T-002 | Archivos: 3
  Archivos: `components/fields/TextField.tsx`, `components/fields/TextField.test.tsx`,
  `components/fields/RequiredLegend.tsx`.
  Hecho cuando: el campo se encuentra por rol y por el texto de su etiqueta; obligatorio, tiene
  `aria-required="true"` y un `*` con `aria-hidden="true"` que no forma parte del nombre accesible;
  de tipo correo, `autocomplete="email"` e `inputmode="email"`; con error, `aria-invalid="true"` y
  una descripción accesible igual al mensaje; sin error, ninguno de los dos; `RequiredLegend`
  muestra el texto traducido que explica el asterisco; suite verde.
  Decisiones: `TextField` recibe la etiqueta y el error ya traducidos (texto, no claves): la página
  que lo usa traduce al pintar, así que un cambio de idioma lo repinta igual (D-05 se cumple en el
  estado del formulario, M-10) — [Probable] — revertir: pasar claves y traducir dentro. Reenvía su
  `ref` al input, para que el foco al primer error (T-022) no necesite tocar el componente —
  [Cierto] — revertir: quitar `forwardRef`. El resto de atributos del input pasan tal cual, pero
  `type`, `required`, `id` y los `aria-*` de accesibilidad los fija el componente — [Cierto] —
  revertir: no aplica.

- [x] T-011 Página de muestra con los campos de texto y correo
  RF: RF-011, RF-019, RF-020 | Depende de: T-009, T-010 | Archivos: 4
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`, `App.tsx`,
  `App.test.tsx`.
  Hecho cuando: el encabezado, la introducción y el selector pasan de `App` a `ShowcasePage`, que
  añade la leyenda del asterisco y un formulario `noValidate` con el campo de texto y el de correo
  obligatorios; `App` solo monta `ShowcasePage` y `useDocumentLanguage`; el test recorre con Tab
  selector → texto → correo en ese orden y comprueba que un valor escrito se conserva al cambiar de
  idioma; suite verde.
  Excepción: mover el contenido de `App` a la página cambia `App` y su test a la vez que la página.
  Decisiones: al final no hizo falta tocar `App.test.tsx`: sus tests siguen valiendo porque `App`
  muestra la página, así que la tarea tocó 3 archivos y no usó la excepción — [Cierto] — revertir:
  no aplica. El formulario se nombra con un encabezado visible `h2` («Formulario de ejemplo») y
  `aria-labelledby` — [Probable] — revertir: `aria-label` sin encabezado. Los campos aún no
  guardan su valor en el estado (el navegador lo conserva al cambiar de idioma); el estado llega
  con la validación (T-019) — [Cierto] — revertir: no aplica. Comprobado en Chromium: orden de Tab
  y valores conservados al pasar a portugués — [Cierto] — revertir: no aplica.

- [x] T-012 Campo de contraseña
  RF: RF-012, RF-024 (D-10) | Depende de: T-010 | Archivos: 2
  Archivos: `components/fields/PasswordField.tsx`, `components/fields/PasswordField.test.tsx`.
  Hecho cuando: `kind` es obligatorio en el tipo (un uso sin `kind` en el test va marcado con
  `@ts-expect-error`); `kind="current"` da `autocomplete="current-password"` y `kind="new"`,
  `new-password`; el control «Mostrar contraseña» se activa con Enter y con Espacio, alterna el
  `type` entre `password` y `text`, cambia `aria-pressed`, conserva el valor y deja el foco en el
  control; suite verde.
  Decisiones: para apoyarse en `TextField` (M-07), este acepta ahora el tipo `password` y un hueco
  `adornment` tras el input, donde va el control; la tarea tocó así 3 archivos en lugar de 2, dentro
  del máximo — [Cierto] — revertir: duplicar la estructura del campo en `PasswordField`. El control
  va después del input, así que en el orden de Tab viene justo detrás del campo — [Probable] —
  revertir: moverlo delante.

- [x] T-013 Contraseña en la página de muestra
  RF: RF-019, RF-020, RF-024 (S-09) | Depende de: T-011, T-012 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página añade un campo de contraseña actual obligatorio tras el correo; el orden
  de Tab es selector → texto → correo → contraseña → «Mostrar contraseña»; suite verde.

- [x] T-014 Auditoría automática de accesibilidad de la página
  RF: RF-006, RF-011, RF-019 (D-13) | Depende de: T-013 | Archivos: 3
  Archivos: `frontend/package.json`, `pnpm-lock.yaml`, `showcase/a11y.test.tsx`.
  Hecho cuando: `axe-core` está en `devDependencies`; el test ejecuta `axe` sobre la página de
  muestra en `es`, `pt-BR` y `en` y falla si hay alguna infracción (comprobado quitando la etiqueta
  de un campo); suite verde.
  Excepción: `pnpm-lock.yaml` lo regenera `pnpm add`; no es un archivo editado a mano.
  Decisiones: la auditoría se ejecuta sobre todo el documento con `App` montada, así que también
  revisa `<html lang>` y las reglas de buenas prácticas de axe (encabezado `h1`, región `main`) —
  [Cierto] — revertir: auditar solo el contenedor. Un segundo test comprueba que la auditoría
  detecta un campo sin etiqueta, para que no pase en verde sin revisar nada. Los tests pasaron
  desde el principio porque la página ya cumplía; lo que demuestra que la auditoría funciona son
  los mutantes (etiquetas desenlazadas y un `aria-checked` no válido en un botón: los dos la hacen
  fallar) — [Cierto] — revertir: no aplica.

- [x] T-015 Normalización del código
  RF: RF-013, RF-014 | Depende de: — | Archivos: 2
  Archivos: `components/fields/code.ts`, `components/fields/code.test.ts`.
  Hecho cuando: `normalizeTypedCode("12a３٤5 67")` devuelve `"123456"`; `extractPastedCode("Tu
  código: 98-76 54 321")` devuelve `"987654"`; `extractPastedCode("sin números")` indica que no hay
  dígitos; suite verde.
  Decisiones: solo se convierten los dígitos de ancho completo (`０`-`９`) y los arábigos
  (`٠`-`٩`) que nombra RF-013; los persas (`۰`-`۹`) y otros sistemas se descartan como cualquier
  otro carácter — [Cierto] — revertir: añadir su primer carácter a la lista de series. La longitud
  se exporta como `CODE_LENGTH` para que el campo y la validación (T-018) usen la misma —
  [Cierto] — revertir: repetir el 6.

- [x] T-016 Campo del código
  RF: RF-013, RF-014, RF-015, RF-016 | Depende de: T-010, T-015 | Archivos: 2
  Archivos: `components/fields/CodeField.tsx`, `components/fields/CodeField.test.tsx`.
  Hecho cuando: un único campo con etiqueta, `inputmode="numeric"` y
  `autocomplete="one-time-code"`; escribir `"1a2b3c4d5e6f7"` deja `"123456"`; pegar `"98 76 54 32"`
  con `"12"` ya escrito y el cursor en medio deja `"987654"`; pegar `"abc"` deja el valor como
  estaba; al llegar a 6 dígitos no se llama a `onSubmit` del formulario y el foco sigue en el campo;
  con error, `aria-invalid` y descripción accesible como en T-010; suite verde.
  Decisiones: `CodeField` reutiliza `TextField` (etiqueta, obligatoriedad, error y `ref`) y guarda
  el código en su propio estado, con `defaultValue` y un aviso `onValueChange` para quien necesite
  el valor (la validación, T-019) — [Probable] — revertir: hacerlo controlado desde fuera con
  `value`. Un mutante sin `preventDefault` en el pegado sobrevivió, porque `user-event` no inserta
  el texto pegado tras el manejador como haría un navegador; se añadió un test que comprueba que el
  pegado por defecto se cancela — [Cierto] — revertir: no aplica.

- [ ] T-017 Código en la página de muestra
  RF: RF-019, RF-020 | Depende de: T-013, T-016 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página añade el campo del código obligatorio tras la contraseña; el orden de Tab
  incluye el código tras «Mostrar contraseña»; la auditoría de T-014 sigue sin infracciones; suite
  verde.

- [ ] T-018 Reglas de validación de la página de muestra
  RF: RF-021 | Depende de: — | Archivos: 2
  Archivos: `showcase/validators.ts`, `showcase/validators.test.ts`.
  Hecho cuando: `required` rechaza `""` y `"   "`; `email` acepta `a@b` y rechaza `a@@b`, `@b`,
  `a@`, `a b@c` y `a@b@c`; `sixDigitCode` rechaza `"12345"` y acepta `"123456"`; cada rechazo
  devuelve una clave de `validation` existente; suite verde.

- [ ] T-019 Validación al salir de cada campo
  RF: RF-016, RF-025 (D-05) | Depende de: T-002 | Archivos: 2
  Archivos: `forms/useFormValidation.ts`, `forms/useFormValidation.test.tsx`.
  Hecho cuando: al salir de un campo, aunque no se haya enviado nada, el hook valida solo ese campo
  y pone o quita su error; los errores se guardan como clave y parámetros; suite verde.

- [ ] T-020 Errores al salir en la página de muestra
  RF: RF-016, RF-018, RF-025 | Depende de: T-017, T-018, T-019 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: salir del correo con `a@` muestra su error, ligado al campo; corregirlo y salir lo
  retira; con un error visible, cambiar a `en` muestra el error en inglés y el campo sigue marcado
  como no válido; suite verde.

- [ ] T-021 Botón
  RF: RF-009 | Depende de: T-002 | Archivos: 2
  Archivos: `components/Button.tsx`, `components/Button.test.tsx`.
  Hecho cuando: el nombre accesible es su texto visible; se activa con clic, Enter y Espacio;
  suite verde.

- [ ] T-022 Validación al enviar y foco al primer error
  RF: RF-021, RF-025, RF-010 | Depende de: T-019 | Archivos: 2
  Archivos: `forms/useFormValidation.ts`, `forms/useFormValidation.test.tsx`.
  Hecho cuando: al enviar valida todos los campos y lleva el foco al primero con error en orden
  visual; sin errores llama al manejador de envío; mientras `processing` está activo, un segundo
  envío no llama al manejador; suite verde.

- [ ] T-023 Mensaje general
  RF: RF-017, RF-018 (D-11) | Depende de: T-002 | Archivos: 2
  Archivos: `components/FormMessage.tsx`, `components/FormMessage.test.tsx`.
  Hecho cuando: cada tipo (`error`, `success`, `info`) muestra su prefijo traducido delante del
  texto; recibe la clave y la traduce al pintar, así que al cambiar de idioma cambia el texto;
  `focus()` lo enfoca y no está en el orden de tabulación; suite verde.

- [ ] T-024 Envío en la página de muestra
  RF: RF-019, RF-020, RF-021 | Depende de: T-020, T-021, T-022, T-023 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: la página añade el botón de envío tras el código; enviar con Enter desde un campo o
  con el botón, con el correo vacío y el código de 5 dígitos, muestra los dos errores y deja el foco
  en el correo; un envío válido muestra el mensaje informativo de demostración y le lleva el foco;
  el orden de Tab completo es selector → texto → correo → contraseña → «Mostrar contraseña» →
  código → enviar; suite verde.

- [ ] T-025 Anunciador
  RF: RF-010, RF-017 (D-08) | Depende de: — | Archivos: 2
  Archivos: `components/LiveAnnouncer.tsx`, `components/LiveAnnouncer.test.tsx`.
  Hecho cuando: las regiones `polite` y `assertive` existen desde el primer renderizado y están
  vacías; `announce("x", "polite")` deja `"x"` solo en la educada tras el siguiente ciclo; anunciar
  dos veces el mismo texto vacía la región entre medias; suite verde.

- [ ] T-026 Botón procesando
  RF: RF-010 (D-07) | Depende de: T-021, T-025 | Archivos: 2
  Archivos: `components/Button.tsx`, `components/Button.test.tsx`.
  Hecho cuando: con `processing`, el texto visible y el nombre accesible son «Procesando…» en el
  idioma activo, tiene `aria-disabled="true"` y no `disabled`, un clic, Enter o Espacio no llama a
  `onClick`, sigue en el orden de Tab y conserva el foco; al entrar en ese estado la región educada
  contiene «procesando»; al salir recupera su texto y no se anuncia nada nuevo; suite verde.

- [ ] T-027 Simulación de envío de 3 segundos
  RF: RF-010, RF-022 | Depende de: T-024, T-026 | Archivos: 3
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`, `App.tsx`.
  Hecho cuando: `App` monta el proveedor del anunciador; con temporizadores simulados, un envío
  válido pone el botón en «procesando» con el foco en él, un segundo envío durante ese tiempo no
  hace nada, y a los 3 segundos (no antes) el botón recupera su texto y el mensaje informativo
  aparece con el foco; suite verde.

- [ ] T-028 Errores de servidor y mensaje general junto a errores de campo
  RF: RF-017, RF-025 (D-14) | Depende de: T-022, T-025 | Archivos: 2
  Archivos: `forms/useFormValidation.ts`, `forms/useFormValidation.test.tsx`.
  Hecho cuando: un error de servidor en un campo se mantiene al salir del campo y se retira en el
  siguiente envío; con error local y de servidor a la vez se muestra el local; con mensaje general
  y sin errores de campo, el foco va al mensaje; con ambos, el foco va al primer campo con error y
  el mensaje se anuncia en la región urgente si es un error y en la educada si no; el mensaje
  general se retira en el siguiente envío; suite verde.

- [ ] T-029 Error general de ejemplo en la página de muestra
  RF: RF-017, RF-018, RF-020 | Depende de: T-027, T-028 | Archivos: 2
  Archivos: `showcase/ShowcasePage.tsx`, `showcase/ShowcasePage.test.tsx`.
  Hecho cuando: el botón «Mostrar error general de ejemplo», último en el orden de Tab, muestra el
  error de demasiados intentos con el prefijo «Error:» y le lleva el foco; cambiar de idioma lo
  traduce sin perderlo; el siguiente envío lo retira; suite verde.

- [ ] T-030 Auditoría de accesibilidad en todos los estados
  RF: RF-016, RF-017, RF-019 (D-13) | Depende de: T-014, T-029 | Archivos: 1
  Archivos: `showcase/a11y.test.tsx`.
  Hecho cuando: `axe` no encuentra infracciones en la página con errores de campo, procesando, con
  el mensaje informativo y con el error general, en los tres idiomas; suite verde.

- [ ] T-031 Resumen y checklist de prueba manual
  RF: RF-019, RF-020 (CF-3, CF-5, S-08) | Depende de: T-030 | Archivos: 2
  Archivos: `specs/componentes-base-accesibles/resumen.md`,
  `specs/componentes-base-accesibles/HUMAN_TODO.md`.
  Hecho cuando: `resumen.md` explica qué se hizo, cómo arrancar y probar la página de muestra, el
  checklist de teclado (CF-3) y de lector de pantalla con NVDA o VoiceOver (CF-5) y el marco
  teórico; `HUMAN_TODO.md` tiene la acción de completar ese checklist.

- [x] T-032 Contraseña visible fuera de correctores y autocorrección
  Tipo: corrección | Origen: revisión de seguridad durante E-04 (D-15)
  RF: RF-012 (D-15) | Depende de: T-012 | Archivos: 2
  Archivos: `components/fields/PasswordField.tsx`, `components/fields/PasswordField.test.tsx`.
  Causa: al mostrar la contraseña el input pasa a `type="text"`, y los correctores del navegador
  o de extensiones pueden leer o enviar su texto, y el teclado móvil, corregirlo.
  Hecho cuando: el input de contraseña tiene `spellcheck="false"`, `autocapitalize="off"` y
  `autocorrect="off"`, tanto oculto como visible; suite verde.

## Entregas
Arrancar la página de muestra (para el «Cómo probarlo» de cada entrega), desde la raíz del
repositorio:
```bash
pnpm install
```
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173. Los tests de cada entrega se ejecutan con:
```bash
pnpm --filter frontend test
```

- E-01 La interfaz sale en el idioma del navegador (español, portugués o inglés; inglés si no
  encaja ninguno), con `lang` y título del documento traducidos.
  Tareas: T-001…T-006 | Líneas estimadas: 470 | Rama: feat/componentes-base-accesibles-traduccion
  Cómo probarlo: con el idioma preferido del navegador en portugués, inglés y francés (en Chrome,
  DevTools → Sensors → Location → Locale), recargar y ver el encabezado en portugués, inglés e
  inglés.
  Excepción: incluye los textos de toda la feature (~130 líneas de datos) para que ninguna tarea
  posterior toque los tres archivos de idioma; sin ellos, la entrega rondaría las 340 líneas.

- E-02 Selector de idioma, usable con teclado, que recuerda la elección.
  Tareas: T-007…T-009 | Líneas estimadas: 320 | Rama:
  feat/componentes-base-accesibles-selector-idioma
  Cómo probarlo: con Tab hasta «English» y Enter, la página pasa a inglés sin recargar y el foco
  sigue en el botón; al recargar, sigue en inglés.

- E-03 Campos de texto y correo con etiqueta, obligatoriedad y asterisco explicado.
  Tareas: T-010, T-011 | Líneas estimadas: 290 | Rama:
  feat/componentes-base-accesibles-campos-texto
  Cómo probarlo: recorrer la página con Tab; escribir en los campos y cambiar de idioma: los
  valores se conservan.

- E-04 Campo de contraseña con mostrar u ocultar y auditoría automática de accesibilidad.
  Tareas: T-012…T-014, T-032 | Líneas estimadas: 230 | Rama:
  feat/componentes-base-accesibles-contrasena
  Cómo probarlo: escribir una contraseña, llegar con Tab a «Mostrar contraseña» y pulsar Espacio:
  se ve el texto y el foco sigue en el control; volver a pulsar la oculta.

- E-05 Campo del código de 6 dígitos.
  Tareas: T-015…T-017 | Líneas estimadas: 270 | Rama: feat/componentes-base-accesibles-codigo
  Cómo probarlo: escribir letras y números (solo quedan los números, hasta 6); pegar «Tu código:
  98-76 54» sobre un código ya escrito (queda «987654»).

- E-06 Errores de campo al salir de cada campo, traducidos al cambiar de idioma.
  Tareas: T-018…T-020 | Líneas estimadas: 330 | Rama:
  feat/componentes-base-accesibles-validacion-al-salir
  Cómo probarlo: escribir «a@» en el correo y pulsar Tab: aparece el error; cambiar a portugués:
  el error se traduce; corregir el correo y salir: el error desaparece.

- E-07 Envío del formulario con foco al primer error y mensaje informativo de demostración.
  Tareas: T-021…T-024 | Líneas estimadas: 380 | Rama: feat/componentes-base-accesibles-envio
  Cómo probarlo: con el formulario vacío, pulsar Enter en un campo: aparecen los errores y el
  foco va al primer campo; con todo válido, enviar: aparece el mensaje de demostración con el foco.

- E-08 Botón «procesando» durante 3 segundos con aviso al lector de pantalla.
  Tareas: T-025…T-027 | Líneas estimadas: 250 | Rama:
  feat/componentes-base-accesibles-procesando
  Cómo probarlo: enviar un formulario válido: el botón dice «Procesando…» 3 segundos, pulsar de
  nuevo no hace nada y el foco no se pierde; después aparece el mensaje de demostración.

- E-09 Mensajes generales de error y cierre de la feature.
  Tareas: T-028…T-031 | Líneas estimadas: 250 | Rama:
  feat/componentes-base-accesibles-errores-generales
  Cómo probarlo: pulsar «Mostrar error general de ejemplo»: aparece «Error: …» con el foco;
  cambiar de idioma lo traduce; enviar de nuevo lo retira. Recorrer el checklist de `resumen.md`
  con NVDA o VoiceOver.

## RF sin tarea
Ninguno.
