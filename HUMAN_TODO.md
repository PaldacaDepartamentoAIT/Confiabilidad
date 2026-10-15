# HUMAN_TODO

Acciones que **requieren intervención humana** (credenciales, instalaciones locales,
binarios, decisiones de infraestructura). Los agentes no las pueden hacer por ti; las
anotan para que no se pierdan. Marca `[x]` cuando completes cada una y muévela a *Hecho*
con la fecha.

Cada feature tiene su propio `specs/<feature>/HUMAN_TODO.md` con lo necesario para
completarla. Este archivo solo recoge las acciones que no pertenecen a ninguna spec (por
ejemplo, las de una rama `chore/` sin feature).

Para ver todo lo pendiente del proyecto, ejecuta desde la raíz del repositorio:
```bash
grep -n -- "- \[ \]" HUMAN_TODO.md specs/*/HUMAN_TODO.md
```
Deberías ver cada acción pendiente con su archivo y su línea.

## Pendiente

Nada pendiente.

## Hecho

- [x] **Entorno remoto en el VPS: tareas de administración** (2026-09-30). Usuario propio con
  `sudo` y `docker` y clave pública instalada, SSH endurecido, swap creada, alta de trabajador
  completada y RAM y disco comprobados. Procedimiento en `README.md` → *Entorno remoto (VPS
  por SSH)*.

- [x] **Dominio con HTTPS para el panel de Coolify** (2026-09-30). Asignado en Settings →
  Instance Domain; las credenciales de administrador ya no viajan en claro.
