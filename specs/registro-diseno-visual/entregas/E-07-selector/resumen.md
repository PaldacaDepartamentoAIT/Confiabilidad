# Entrega E-07 · Selector de país con lista propia

Rama: `feat/registro-diseno-visual-selector` (apilada sobre `feat/registro-diseno-visual-ayuda`,
E-06) · PR: pendiente · Líneas de código y tests: 679 (límite: 400; máximo con excepción: 500, por
encima hay que dividir o decidir el usuario).

## Qué se hizo
- **Búsqueda al teclear** (`forms/typeahead.ts`, T-025): escribir las primeras letras salta a la
  primera opción que empieza así, sin distinguir mayúsculas ni tildes; las teclas pulsadas en menos
  de 500 ms se acumulan; repetir una letra recorre las opciones que empiezan por ella.
- **Validación con botones** (`forms/useFormValidation.ts`, T-026): el envío y el foco leen el valor
  de un botón con `name` y `value`, como el de un campo.
- **Selector propio** (`components/fields/SelectField.tsx`, T-027): un botón `role="combobox"` con la
  flecha que gira al abrirse; la lista (`role="listbox"`) solo existe mientras está abierta. Teclado:
  Intro, Espacio o flechas abren; flechas, Inicio, Fin, Re Pág y Av Pág recorren; Intro elige; Escape
  cierra sin cambiar nada; Tab elige la resaltada y sigue. Un clic en una opción no quita el foco.
- **País en el registro** (T-028): el formulario usa el selector nuevo.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-025 | Búsqueda al teclear | `8206da9` |
| T-026 | La validación lee un botón con valor | `d6a6ff7` |
| T-027 | Selector con lista propia | `2a930c5` |
| T-028 | País con el selector propio | `2a930c5`, `fe63d21` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (472). Levanta el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register, pulsa el selector de «País»: se despliega la lista con la
flecha girada. Teclea «pe»: se resalta Perú. Intro lo elige y la lista se cierra. Con Escape, la
lista se cierra sin cambiar nada.
