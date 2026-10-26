# Entrega E-04 · Contraseña con mostrar u ocultar y auditoría de accesibilidad

Rama: `feat/componentes-base-accesibles-contrasena`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#24](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/24) ·
Líneas de código y tests: 154 (límite: 400).

## Qué se hizo
- Un campo de contraseña que se apoya en el campo de texto (misma etiqueta, asterisco y errores):
  - quien lo use debe indicar si es la contraseña **actual** o una **nueva**: sin esa indicación,
    el código no compila. Con ella, el navegador y los gestores de contraseñas saben si rellenar la
    guardada o proponer una nueva segura;
  - tiene un botón «Mostrar contraseña», justo detrás del campo en el orden de Tab, que se activa
    con Enter, Espacio o clic. Alterna entre ver y ocultar lo escrito, sin perderlo y sin mover el
    foco. El lector anuncia el botón como «presionado» mientras la contraseña está visible.
- La página de muestra añade el campo «Contraseña» (contraseña actual, obligatoria) después del
  correo.
- Una auditoría automática con axe revisa la página entera en español, portugués e inglés, y la
  suite falla si encuentra una infracción de accesibilidad: campos sin etiqueta, ARIA mal usado,
  `id` repetidos, idioma del documento ausente o no válido, entre otras.
- Dependencia nueva de desarrollo: `axe-core`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-012 | Campo de contraseña | `0a36fc2` |
| T-013 | Contraseña en la página de muestra | `03dcc19` |
| T-014 | Auditoría automática de accesibilidad de la página | `91f6ceb` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend, incluida la auditoría de accesibilidad:
```bash
pnpm --filter frontend test
```
Deberías ver 57 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el campo «Contraseña *» y el botón «Mostrar
contraseña».

Pruébalo solo con el teclado:
1. Pulsa Tab hasta el campo «Contraseña» y escribe algo. Deberías ver puntos en lugar del texto.
2. Pulsa Tab una vez. El foco pasa al botón «Mostrar contraseña».
3. Pulsa Espacio. Deberías ver lo que escribiste en claro, con el foco todavía en el botón.
4. Pulsa Espacio otra vez. Deberías volver a ver puntos, con el mismo texto.

En DevTools (F12) → **Elements** → **Accessibility**, con el botón seleccionado, deberías ver
**Pressed** en `true` mientras la contraseña está visible y en `false` cuando está oculta.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Fuera de esta entrega
El campo del código de 6 dígitos llega en E-05; la validación, el envío y los mensajes generales,
de E-06 a E-09.
