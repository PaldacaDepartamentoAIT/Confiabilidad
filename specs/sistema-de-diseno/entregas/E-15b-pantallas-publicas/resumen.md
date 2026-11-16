# Entrega E-15b · Pantallas públicas con la columna de la guía

Rama: `feat/sistema-de-diseno-pantallas-publicas` (sale de `feat/sistema-de-diseno`) · PR: [#99](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/99) ·
Líneas de código y tests: 168 (límite: 400).

## Qué se hizo
- Las pantallas sin sesión (registro, verificación del código, enlace no válido y cuenta creada) ya no
  son una caja a todo el ancho: llevan una columna centrada de 480 px como máximo (el ancho completo en
  pantallas estrechas), con 22 px de relleno lateral y 32 px de margen superior.
- Dentro hay un único bloque cuya cabecera es el título de la pantalla (`h1`, 15 px, 600); debajo van el
  texto, los campos apilados con 16 px de separación y la acción a la derecha.
- «Enviar otro código» pasa a ser un botón secundario, porque es la acción secundaria de la pantalla.
- La guía (`docs/identidad-visual.md`) y RF-005 describen ahora esta columna; el flujo, los textos y las
  validaciones de las pantallas no cambian.
- Verificado en un navegador real con la API simulada, a 1000 y 420 px: el formulario de registro, la
  verificación y la cuenta creada se ven como un bloque centrado.
- Quedan unas reglas transitorias que anulan la caja de `main`, `form` y `section`; se retiran en E-15c.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-070 | Columna de las pantallas públicas | `ca4d633` |
| T-071 | Registro con la columna pública | `460efd7` |
| T-072 | Verificación, enlace no válido y cuenta creada con la columna pública | `9cd9ea6` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 56 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register: verás el formulario dentro de un bloque centrado de 480 px con su
título. Abre http://localhost:5173/register/done para ver la pantalla de cuenta creada. Estrecha la
ventana y el bloque ocupa todo el ancho.

## Marco teórico
- **Columna de lectura:** un formulario de una sola columna y de ancho limitado es más fácil de
  recorrer que uno a todo el ancho de la pantalla; la vista no tiene que saltar de un extremo a otro.
- **Un solo bloque por pantalla:** agrupar el título, el texto y el formulario en el mismo bloque deja
  claro qué pertenece a qué y reutiliza el mismo elemento visual que el resto del sistema.
