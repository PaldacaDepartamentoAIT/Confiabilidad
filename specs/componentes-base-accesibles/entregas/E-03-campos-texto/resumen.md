# Entrega E-03 · Campos de texto y correo en la página de muestra

Rama: `feat/componentes-base-accesibles-campos-texto`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#23](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/23) ·
Líneas de código y tests: 215 (límite: 400).

## Qué se hizo
- Un componente de campo de texto, que también sirve para correo:
  - su etiqueta visible es el nombre que lee el lector de pantalla;
  - si es obligatorio, la etiqueta lleva un `*` visible que el lector no lee (solo anuncia
    «obligatorio»);
  - el de correo pide al navegador el autocompletado de correo y, en móvil, el teclado con `@`;
  - si el campo tiene un error, el mensaje aparece debajo, queda ligado al campo (el lector lo lee
    al llegar a él) y el campo se marca como no válido; al quitar el error, desaparecen las dos
    cosas.
- Un texto visible que explica el asterisco («Los campos marcados con * son obligatorios.»).
- La página de muestra: el selector de idioma, el encabezado, la introducción y un «Formulario de
  ejemplo» con los campos «Nombre completo» y «Correo electrónico», los dos obligatorios. Al cambiar
  de idioma se conserva lo escrito.
- Todavía no hay validación ni botón de envío: los errores de campo ya están preparados en el
  componente, pero la página aún no los muestra (llegan en E-06).

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-010 | Campo de texto y de correo | `12f3dd9` |
| T-011 | Página de muestra con los campos de texto y correo | `9310117` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 49 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173, con el selector de idioma, el encabezado y el
«Formulario de ejemplo».

Pruébalo solo con el teclado:
1. Haz clic en la barra de direcciones y pulsa Tab cinco veces. Deberías recorrer «Español»,
   «Português (Brasil)», «English», «Nombre completo *» y «Correo electrónico *», en ese orden.
2. Escribe tu correo y pulsa Mayús+Tab para volver a «Nombre completo». Escribe un nombre.
3. Pulsa Mayús+Tab hasta «English» y luego Enter. Deberías ver las etiquetas en inglés («Full
   name», «Email») con lo que escribiste intacto.

Para ver lo que anuncia un lector de pantalla sin instalar uno, en Chrome abre DevTools (F12) →
**Elements**, selecciona un campo y abre la pestaña **Accessibility**. Deberías ver que su
**Name** es la etiqueta sin el asterisco y que **Required** es `true`.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Comprobado por el usuario en local el 2026-10-28.

## Fuera de esta entrega
El campo de contraseña llega en E-04 y el del código en E-05.
