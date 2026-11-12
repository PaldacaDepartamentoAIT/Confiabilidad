# Entrega E-03 · Casilla con enlace y casilla del modal

Rama: `feat/casilla-con-documento-casilla-enlace` (sale de `feat/casilla-con-documento`) · PR: [#108](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/108) ·
Líneas de código y tests: 347 (límite: 400).

## Qué se hizo
- Hay un componente reutilizable `DocumentCheckbox`, sin nada propio del registro (recibe etiqueta, documento,
  nombre y los manejadores del formulario). Con documento, el texto de la casilla es un enlace
  (`aria-haspopup="dialog"`) que abre el modal sin marcar la casilla. Pulsar el cuadro marca o desmarca la
  casilla sin abrir nada. Pulsar cualquier otra parte de la fila no hace nada, porque el texto no va envuelto
  en una etiqueta `<label>`.
- Sin documento (texto vacío o ausente), es una casilla normal, sin enlace ni modal.
- El pie del modal lleva una casilla con el mismo texto (y el asterisco si es obligatoria): marcarla o
  desmarcarla cambia también la de fuera y el modal sigue abierto. La casilla del modal está fuera del
  formulario y no tiene nombre, así que no entra en sus datos; solo se envía la de fuera.
- El estado es de la casilla: se conserva al cerrar y volver a abrir el modal, y cualquier cambio avisa al
  `onChange` del formulario.
- Todavía no se ve en el catálogo ni muestra error ni ayuda: llegan en E-03b.
- Esta parte salió de una entrega de 670 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-008 | Casilla con enlace al documento | `8b84194` |
| T-009 | Casilla del modal sincronizada | `6476c3a` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 61 archivos de test en verde, entre ellos `DocumentCheckbox.test.tsx` (21 tests).

## Marco teórico
- **Estado compartido (controlado):** las dos casillas no guardan cada una su estado; las dos leen y escriben el
  mismo estado del componente. Así no hay forma de que se desincronicen.
- **Por qué no una etiqueta `<label>`:** una etiqueta marca su casilla al pulsar cualquier parte de ella. Como
  aquí el texto es un enlace que abre otra cosa, la fila no debe actuar como etiqueta.
