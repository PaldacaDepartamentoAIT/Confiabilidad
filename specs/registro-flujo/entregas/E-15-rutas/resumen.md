# Entrega E-15 · Registro completo en la web

Rama: `feat/registro-flujo-rutas` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#54](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/54) ·
Líneas de código y tests: 268 (límite: 400).

## Qué se hizo
- **Rutas del registro** (`frontend/src/App.tsx`): `/register`, `/register/continue` y
  `/register/done` muestran sus pantallas; `/` y cualquier otra ruta siguen con la página de muestra.
  La aplicación crea el cliente de la API según el entorno (web o Tauri).
- **Accesibilidad** (`frontend/src/registration/a11y.test.tsx`): `axe-core` no encuentra fallos en el
  formulario (vacío y con errores), la verificación (normal, bloqueada y enlace no válido), el paso
  de contraseña y la cuenta creada, y ninguna pantalla posterior al formulario contiene un correo.
- **Dos fallos encontrados al recorrer el registro en Chromium**, corregidos con tareas aprobadas:
  - T-054: el proxy de desarrollo de Vite reescribía la cabecera `Host` y todos los `POST` de la web
    daban `403` por CSRF. Ahora conserva el `Host` del navegador;
  - T-055: si un campo con error perdía el foco al pulsar otro control, su error aparecía o
    desaparecía antes de soltar el botón y el clic se perdía. Ahora la validación espera a que el
    clic termine.
- **Resumen de la feature** (`specs/registro-flujo/resumen.md`), con el recorrido en la web y con
  `curl` comprobados contra el backend local, la limpieza y los límites conocidos. El `HUMAN_TODO.md`
  de `cambio-contrasena` indica que los límites del registro ya existen.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-051 | Rutas del registro | `f6296fa` |
| T-052 | Accesibilidad de las pantallas del registro | `516787e` |
| T-054 | Proxy de desarrollo que conserva el origen | `f044244` |
| T-055 | Validación al salir que no mueve un clic en curso | `3a87e27` |
| T-053 | Resumen de la feature y límites pendientes | `b6619df` |

## Cómo ejecutarlo y probarlo
Sigue «Cómo probarlo» de [`resumen.md`](../../resumen.md): el registro en
http://localhost:5173/register de principio a fin, con el código que muestra la consola del worker, y
el mismo recorrido con `curl`.

Ejecuta también la suite del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 368 tests en verde.

## Marco teórico
Los conceptos de esta entrega (CSRF y el proxy de desarrollo, el clic que se pierde por un
desplazamiento) están explicados en el «Marco teórico» de [`resumen.md`](../../resumen.md).
