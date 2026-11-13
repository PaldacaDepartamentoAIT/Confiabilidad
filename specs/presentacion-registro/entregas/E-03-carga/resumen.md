# E-03 Registro con carga y fundido

## Qué se hizo
La pantalla de registro ya no muestra una card vacía mientras carga sus opciones: no pinta nada hasta que llega
la respuesta y entonces la card entra con un fundido de 0,2 s. Si la carga falla, o pasan 10 s sin respuesta,
aparece la card con el error de conexión y una respuesta que llegue después se ignora. Con movimiento reducido
no hay fundido (lo anula la regla global de `base.css`). Se añaden además dos piezas que usará la entrega
siguiente: `Fade` (fundido al cambiar de paso dentro de la card) y `useDeadline` (plazo). El flujo, los textos
y las validaciones no cambian.

## Tareas
- T-006 (fundido de la card y carga lista) — commit `ef7e51e`.
- T-007 (fundido de un contenido que cambia dentro de la card) — commit `020d9a7`.
- T-008 (plazo de 10 s) — commit `4e8b9b1`.
- T-009 (registro con carga, plazo y fundido) — commit `2f54f41`.

## Cómo ejecutarlo y probarlo
```bash
pnpm --filter frontend test
```

Deberías ver 823 pruebas en verde.

Para verlo en el navegador, arranca el frontend:

```bash
pnpm --filter frontend dev
```

Abre `/register` con la conexión normal para comprobar que carga. En las herramientas de desarrollo, abre
«Bloqueo de solicitudes de red» (menú ⋮, «Más herramientas») y añade el patrón `*registration/options*`; recarga la
página. Deberías ver la barra superior desde el principio, sin card ni título, y enseguida la card con el error de
conexión. No uses «Offline» antes de recargar: corta también la carga de la propia página y el navegador muestra
su pantalla de error. El plazo de 10 s lo cubren los tests con temporizadores simulados, y el fundido y el
movimiento reducido se comprueban en Chromium en la tarea T-013 (entrega E-04).

## Líneas
271 de código y pruebas (límite 400).

## PR
Pendiente.
