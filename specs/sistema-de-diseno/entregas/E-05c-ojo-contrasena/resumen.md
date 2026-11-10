# Entrega E-05c · Botón de ojo dentro del campo de contraseña

Rama: `feat/sistema-de-diseno-ojo-contrasena` · PR: [PaldacaDepartamentoAIT/Confiabilidad#75](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/75) ·
Líneas de código y tests: 92 (límite: 400).

## Qué se hizo
- Este cambio lo pidió el usuario después de E-05: el botón para mostrar u ocultar la contraseña
  deja de ser un botón secundario con texto bajo el campo y pasa a ser un ojo dentro del campo, a la
  derecha, porque es lo que los usuarios esperan y ocupa menos espacio.
- El ojo abierto indica que la contraseña está oculta y el ojo tachado, que se está viendo. Es un
  botón real de 32 × 32 px con el icono de 16 px en texto secundario (tinta al pasar el cursor), y
  mantiene su nombre accesible («Mostrar contraseña (Contraseña)»), `aria-pressed`, el foco y el
  teclado (Intro y Espacio). El campo deja sitio a la derecha para que el texto no quede bajo el
  botón. No cambia el comportamiento: campo y botón siguen contando como uno al validar al salir.
- El módulo de iconos tiene dos iconos más (ojo y ojo tachado), de la misma librería ya instalada.
- La guía `docs/identidad-visual.md` tiene una línea nueva sobre botones de icono dentro de un campo.
- Mide 32 × 32 px y no 36 × 36 px, porque dentro de un campo de 36 px con borde de 1 px un botón de
  36 px taparía el borde.
- Dos fallos que solo se veían en un navegador real se corrigieron antes de entregar: el relleno
  de la regla transitoria de `button` aplastaba el icono y su regla de `aria-pressed` pisaba el color.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-056 | Iconos de ojo en el módulo de iconos | `dc26c02` |
| T-057 | Botón de ojo dentro del campo de contraseña | `cfc4263` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 38 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, escribe algo en «Password» y pulsa el ojo (o llega con Tab y pulsa
Intro): el texto debe verse y el icono pasar a ojo tachado; al volver a pulsarlo, se oculta.

## Marco teórico
- **Botón de icono sin texto visible:** el icono es decoración; lo que lee el lector de pantalla es
  el nombre accesible del botón («Mostrar contraseña (Contraseña)»). `aria-pressed` indica si el
  botón está activado, para que también se entienda que alterna un estado.
- **Tamaño del área pulsable:** la guía WCAG 2.2 pide al menos 24 × 24 px; el botón mide 32 × 32 px
  para que sea cómodo con el dedo sin tapar el borde del campo.
