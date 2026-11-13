# E-04b Prueba de la carga, el fundido y la barra en Chromium

## Qué se hizo
Pruebas en un navegador real (Chromium, tema claro y oscuro, API simulada y retenida) de las pantallas públicas
del registro: mientras se espera la respuesta no hay card ni título y la barra superior sí está; al llegar, la
card entra con un fundido de 0,2 s; pasados 10 s sin respuesta aparece con el error de conexión; con movimiento
reducido no hay animación; la barra es el mismo nodo al cambiar de pantalla; y `axe`, con contraste, no halla
violaciones. La guía visual recoge el fundido. No cambia código de la aplicación.

## Tareas
- T-013 (prueba en Chromium: carga, fundido, barra y movimiento reducido) — commit de esta entrega.

## Cómo ejecutarlo y probarlo
```bash
pnpm --filter frontend test:visual
```

Deberías ver 74 pruebas visuales en verde, 34 de ellas en `registration.visual.test.ts`.

Para comprobar que detecta fallos, cambia en `frontend/src/layouts/PublicPage.css` `0.2s` por `0.5s` en la
animación `public-in` y vuelve a ejecutar el comando anterior: deben fallar las pruebas del fundido.

## Líneas
Ver el PR.

## PR
Pendiente.
