# E-02b Prueba de la verificación en Chromium

## Qué se hizo
Se añadió una prueba en un navegador real (Chromium, tema claro y oscuro, API simulada) que fija lo que la
entrega E-02 cambió en la pantalla de verificación: los botones en una fila, el aspecto de un botón bloqueado y
el hueco reservado del mensaje de reenvío. La guía visual recoge las acciones de un formulario y el hueco de
mensajes. No cambia código de la aplicación.

## Tareas
- T-005 (prueba en Chromium: botones, desactivado y altura de la verificación) — commit de esta entrega.

## Cómo ejecutarlo y probarlo
```bash
pnpm --filter frontend test:visual
```

Deberías ver las 56 pruebas visuales en verde, 16 de ellas en `registration.visual.test.ts`.

Para comprobar que la prueba detecta fallos, cambia en `frontend/src/registration/verify.css` `gap:10px` por
`gap:14px` y vuelve a ejecutar el comando anterior: debe fallar «los dos botones van en la misma fila».

## Líneas
Unas 160 líneas de código y pruebas (límite 400).

## PR
Pendiente.
