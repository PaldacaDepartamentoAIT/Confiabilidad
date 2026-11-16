# Entrega E-07b · Selector propio y su sección en el catálogo

Rama: `feat/sistema-de-diseno-selector-propio` · PR: [PaldacaDepartamentoAIT/Confiabilidad#79](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/79) ·
Líneas de código y tests: 322 (límite: 400).

## Qué se hizo
- Hay un selector propio que se ve como un campo de formulario: etiqueta, disparador de 36 px a todo
  el ancho de su contenedor con el valor a la izquierda y un chevron a la derecha, ayuda y error con
  icono. Sin valor muestra su texto de reserva en texto secundario. Al abrirlo despliega la lista
  sobre el menú compartido, con la opción actual en negrita y con chevron, y se maneja con ratón y con
  teclado (flechas, Inicio, Fin, Intro, Espacio, Escape y escribir para saltar a una opción).
- El disparador es un botón con `name` y `value`, de modo que el formulario lo lee y lo enfoca como
  cualquier otro campo. Acepta valor inicial o controlado, avisa de cada cambio y pasa el `ref` y el
  `onBlur` al botón. Para el lector de pantalla es un `combobox` con su etiqueta, `aria-required`,
  `aria-invalid` y la ayuda y el error como descripción.
- La sección «Campos» del catálogo exhibe dos: «Sector», con valor, y «Tipo de planta», con error.
  Medido en un navegador real: 36 px de alto, borde de 1 px, hover en el color principal y borde de
  2 px con 10 px de relleno al abrirlo, en claro y oscuro.
- Aún no sustituye al `<select>` nativo del registro: eso, junto con el nativo en dispositivos
  táctiles, llega en E-07c. Esta parte salió de la entrega del selector, que medía 594 líneas.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-023 | Selector propio | `c3f7ef0` |
| T-025 | Catálogo: selector | `35e16d2` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 41 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Campos», abre «Sector» con un clic o con Tab e Intro, elige
otra opción con las flechas o escribiendo («t» salta a «Transmisión») y comprueba que el valor
cambia; pulsa el botón de tema para verlo en claro y oscuro.

## Marco teórico
- **Selector que parece un campo:** el disparador reutiliza las mismas reglas de un campo de texto
  (altura, borde, hover y foco), de modo que un formulario con textos y selectores se ve uniforme.
- **Botón con `name` y `value`:** un botón puede llevar nombre y valor como un campo; el formulario
  de la aplicación los lee igual que lee un `input`, sin código especial para el selector.
