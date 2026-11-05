# Entrega E-06 · Ayuda «?» en los campos del registro

Rama: `feat/registro-diseno-visual-ayuda` (apilada sobre `feat/registro-diseno-visual-mensajes`,
E-05) · PR: [PaldacaDepartamentoAIT/Confiabilidad#65](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/65) · Líneas de código y tests: 367 (límite: 400).

## Qué se hizo
- **Descripciones** (T-019): una por campo (nombre, fecha de nacimiento, correo, país, código y
  contraseña) en español, inglés y portugués. Ninguna revela si un correo tiene cuenta.
- **Botón «?» con su globo** (`HelpTip`, T-020): botón circular junto al nombre del campo. El globo
  se abre al pasar el puntero, al llegar con el teclado o al tocarlo, y se cierra al irse el puntero
  o el foco, con otro toque o con Escape.
- **El campo lee su descripción** (T-021, T-022): el lector de pantalla la oye al llegar al campo,
  antes de la ayuda visible y del error, aunque nunca se abra el globo.
- **En el registro** (T-023, T-024): nombre, fecha, correo, país, código y contraseña llevan su
  «?». Las casillas y la página de muestra no. La contraseña sigue mostrando sus reglas debajo.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-019 | Descripciones de los campos | `ead4cf8` |
| T-020 | Botón «?» con globo | `5475eb9` |
| T-021 | El campo lleva su «?» y lee su descripción | `b3c6a83` |
| T-022 | «?» en el selector | `c33b7ff` |
| T-023 | «?» en el formulario de registro | `9999e0e` |
| T-024 | «?» en el código y la contraseña | `593fef6` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (449). Levanta todo el entorno:
```bash
docker compose -f docker/docker-compose.yml up
```
Abre http://localhost:5173/register y pasa el puntero por el «?» de «Correo electrónico»: aparece el
globo con su descripción. Llega con Tab al «?»: se abre; pulsa Escape: se cierra. En un móvil, tócalo
para abrirlo y otra vez para cerrarlo.
