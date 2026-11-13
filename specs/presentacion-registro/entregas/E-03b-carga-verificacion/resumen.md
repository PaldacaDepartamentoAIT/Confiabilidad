# E-03b Verificación y cuenta creada con carga y fundido

## Qué se hizo
La pantalla de verificación no muestra una card vacía mientras carga el estado: no pinta nada hasta que llega la
respuesta y entonces la card entra con fundido. Si falla, o pasan 10 s sin respuesta, aparece la card con el
error de conexión y una respuesta posterior se ignora. El cambio del código a la contraseña entra con el mismo
fundido, y el enlace no válido y la cuenta creada entran con el de su card. El flujo, los textos y las
validaciones no cambian.

## Tareas
- T-010 (verificación y enlace no válido con carga, plazo y fundido) — commit de esta entrega.
- T-011 (cuenta creada con fundido) — commit de esta entrega. No cambia código: `DonePage` ya recibe el fundido
  de la card desde E-03; la tarea añade su test.

## Cómo ejecutarlo y probarlo
```bash
pnpm --filter frontend test
```

Deberías ver 833 pruebas en verde.

Para verlo en el navegador, arranca el frontend:

```bash
pnpm --filter frontend dev
```

Abre `/register/continue#<PUBLIC_ID>` con la conexión normal (el identificador sale del enlace del correo de
verificación). En las herramientas de desarrollo, «Bloqueo de solicitudes de red» (menú ⋮, «Más herramientas»),
añade `*registration/status*` y recarga: deberías ver la barra superior, sin card, y enseguida la card con el
error de conexión. No uses «Offline» antes de recargar: corta también la carga de la página. El fundido y el
movimiento reducido se comprueban en Chromium en la tarea T-013 (entrega E-04).

## Líneas
Ver el PR.

## PR
Pendiente.
