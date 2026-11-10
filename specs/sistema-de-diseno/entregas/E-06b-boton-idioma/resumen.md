# Entrega E-06b · Botón de idioma y catálogo

Rama: `feat/sistema-de-diseno-boton-idioma` (sale de `feat/sistema-de-diseno-menu`) · PR: pendiente ·
Líneas de código y tests: 251 (límite: 400).

## Qué se hizo
- Hay un botón de idioma que muestra el código del idioma activo («ES», «PT» o «EN») con un icono de
  globo y, al pulsarlo, abre un menú con los tres idiomas, cada uno con su nombre en su idioma
  («Español», «Português (Brasil)», «English»). Elegir uno cambia la interfaz, el código del botón y
  su nombre, y recuerda la elección. Se maneja igual con el teclado que el menú compartido de E-06.
  Para el lector de pantalla se llama, por ejemplo, «Idioma: Español».
- La página de muestra tiene una sección nueva, «Menú e idioma», con el botón de idioma real y un
  menú genérico de plantas que recuerda la opción elegida, en claro y oscuro. Su contenido de
  ejemplo es inventado y está en español, marcado como tal.
- El selector de idioma de tres botones que ya existe se mantiene sin cambios; el botón de idioma es
  el que se usará en la barra superior y el menú lateral.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-020 | Botón de idioma | `a5b8b68` |
| T-021 | Catálogo: menú e idioma | `80c3b28` |

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
Abre http://localhost:5173/, baja hasta «Menú e idioma», pulsa el botón de idioma (o llega con Tab y
pulsa Intro), elige otro idioma con el ratón o con las flechas y comprueba que cambia el texto de la
página y el código del botón.

## Marco teórico
- **Nombre accesible del botón de idioma:** el botón solo muestra «ES», que no dice nada a un lector
  de pantalla; por eso su nombre es «Idioma: Español», formado con el texto «Idioma» ya traducido y
  el nombre del idioma activo en su propio idioma. No hizo falta añadir textos nuevos.
