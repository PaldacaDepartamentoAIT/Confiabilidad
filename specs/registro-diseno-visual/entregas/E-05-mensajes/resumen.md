# Entrega E-05 · Mensajes de cada paso en su sitio reservado

Rama: `feat/registro-diseno-visual-mensajes` (apilada sobre `feat/registro-diseno-visual-campos`,
E-04) · PR: [PaldacaDepartamentoAIT/Confiabilidad#64](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/64) · Líneas de código y tests: 150 (límite: 400).

## Qué se hizo
- **Zona de mensajes** (`MessageZone`, T-016): un hueco de una línea, siempre presente, justo encima
  del botón principal de cada paso. Si el mensaje ocupa más, se ve entero.
- **Formulario y contraseña** (T-017): el mensaje general (fallo de red o del servidor) y el aviso
  de espera por límite van en la zona, encima de «Continuar» y de «Crear cuenta».
- **Verificación** (T-018): el tiempo restante del código (o el aviso de caducado), el mensaje de
  código rechazado, el de bloqueo tras cinco intentos, el aviso de espera y el mensaje general van
  en la zona, encima de «Verificar». Los avisos del reenvío siguen junto a su propio botón.

El foco y los anuncios al lector de pantalla no cambian: siguen las reglas de `registro-flujo`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-016 | Zona de mensajes | `2c6d4a0` |
| T-017 | Mensajes del formulario y de la contraseña en la zona | `818b24a` |
| T-018 | Mensajes de la verificación en la zona | `0dad46b` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (438). Para verlo en el navegador, levanta solo el frontend, sin el
backend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register: como no hay backend, verás el aviso de que no se pudo conectar.
Para ver la zona en la verificación, levanta todo el entorno:
```bash
docker compose -f docker/docker-compose.yml up
```
Regístrate en http://localhost:5173/register: en la pantalla de verificación, «El código caduca
en 15:00.» aparece justo encima de «Verificar» y, si escribes cinco códigos erróneos, el aviso de
bloqueo ocupa ese mismo sitio sin mover el campo.
