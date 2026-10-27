# Entrega E-09 · Mensajes generales de error y cierre de la feature

Rama: `feat/componentes-base-accesibles-errores-generales`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR: pendiente · Líneas de código y tests: 403 (límite: 400;
excepción aprobada, anotada en la entrega E-09 de [`tasks.md`](../../tasks.md)).

## Qué se hizo
- El **hook de validación** acepta la respuesta del servidor con `showResult`:
  - errores por campo, que se mantienen al salir del campo y se retiran en el siguiente envío; si
    el usuario provoca un error local en ese campo, se ve el local;
  - un mensaje general (error, éxito o información) que se retira en el siguiente envío;
  - el foco: sin errores de campo, va al mensaje general; con ellos, va al primer campo con error
    y el mensaje se anuncia sin mover el foco, por la región urgente si es un error y por la
    educada si no.
- La **página de muestra** tiene el botón «Mostrar error general de ejemplo», el último en el
  orden de Tab, que muestra «Error: Demasiados intentos. Espera unos minutos y vuelve a
  intentarlo.» con el foco. El mensaje de demostración de E-08 usa ahora el mismo camino.
- La **auditoría de accesibilidad** (axe) recorre la página con errores de campo, procesando, con
  el mensaje de demostración y con el error general, en los tres idiomas.
- El **resumen de la feature** ([`resumen.md`](../../resumen.md)), con los checklists de teclado y
  de lector de pantalla y el marco teórico, y la acción de completarlos en
  [`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-028 | Errores de servidor y mensaje general junto a errores de campo | `1b84307` |
| T-029 | Error general de ejemplo en la página de muestra | `447d573` |
| T-030 | Auditoría de accesibilidad en todos los estados | `15b6356`, `a9f0331` |
| T-031 | Resumen y checklist de prueba manual | `c40754b` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 185 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el formulario de ejemplo.

Pruébalo con el teclado:
1. Pulsa Tab hasta «Mostrar error general de ejemplo», el último control, y pulsa Enter. Deberías
   ver «Error: Demasiados intentos. Espera unos minutos y vuelve a intentarlo.» sobre el formulario,
   con el foco en él.
2. Pulsa «English». Deberías ver el mensaje en inglés: «Error: Too many attempts. Wait a few minutes
   and try again.».
3. Pulsa Tab hasta «Verify» y pulsa Enter con el formulario vacío. Deberías ver que el mensaje
   desaparece y que el foco va a «Full name» con su error.
4. Con el ratón: escribe `12` en el código, sal del campo, complétalo con `123456` y pulsa «Mostrar
   error general de ejemplo». Deberías ver el error general con el foco, aunque el error del código
   desaparezca al pulsar.

El resto, con un lector de pantalla, está en los checklists de [`resumen.md`](../../resumen.md).

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).
