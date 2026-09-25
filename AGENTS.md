# AGENTS.md — Confiabilidad

## Proyecto
Herramienta (web y de escritorio) para la gestión de activos en instalaciones
industriales, basada en la filosofía de Confiabilidad Operacional.

Stack: Django REST Framework + Channels (WebSocket) + Celery/Redis en el backend;
React + TypeScript (Vite) en el frontend web; Tauri (Rust) como cliente de escritorio
que envuelve la app web. Todo dockerizado; secretos de producción cifrados con SOPS + age.

## Estructura
- `backend/`  — Django + DRF + Channels + Celery.
- `frontend/` — única app React (Vite). Toda la UI vive aquí.
- `desktop/`  — Tauri (Rust); carga el dev server / build de `frontend/`, no duplica React.
- `docker/`   — docker-compose y entrypoints.
- `secrets/`  — variables de entorno cifradas con SOPS/age.
- `specs/`    — artefactos SDD (ver Rutas).

## Comandos
Entorno reproducible con Docker (fuente de verdad):
- Levantar todo: `docker compose -f docker/docker-compose.yml up`
- Backend (dentro del contenedor o venv): `python manage.py runserver` (HTTP) / servidor ASGI para WebSocket
- Celery worker: `celery -A config worker -l info`
- Celery beat: `celery -A config beat -l info`
- Frontend web: `pnpm --filter frontend dev`
- Desktop (Tauri): `pnpm --filter desktop tauri dev`

Tests:
- Backend: `pytest`
- Frontend: `pnpm --filter frontend test`  (Vitest)

Tipos:
- Backend: `mypy backend/`  (modo estricto)
- Frontend/Desktop: `pnpm --filter frontend typecheck`  (`tsc --noEmit`, modo strict)

Lint / formato:
- Backend: `ruff check .` y `black .`
- Frontend/Desktop TS: `pnpm lint` (ESLint) y `pnpm format` (Prettier)
- Rust: `cargo fmt` y `cargo clippy`

Secretos:
- Desarrollo: `.env` local (gitignoreado) con valores de dev; `.env.example` versionado
  como plantilla (claves sin valores reales). Docker Compose lo carga con `env_file:`.
- Producción: secretos reales cifrados con SOPS + age. Editar: `sops secrets/prod.enc.yaml`.
- `.env` nunca se commitea; en el repo solo van archivos `*.enc.*` cifrados y `.env.example`.

## Estilo y convenciones
- Código en inglés, según la convención de cada lenguaje:
  - Python: PEP 8, snake_case, tipado estático (mypy estricto).
  - TS/React: camelCase, componentes en PascalCase, TypeScript en modo strict, ESLint + Prettier.
  - Rust: convención estándar (snake_case), rustfmt + clippy.
- Comentarios en español, solo si son imprescindibles para entender el proceso
  o si el usuario los pide. Nada de comentarios obvios.
- Estructura y código limpios: cada carpeta (backend / frontend / desktop) es
  independiente y no invade a las demás.

## Ramas (branches)
- Formato: `tipo/descripcion-corta` — todo en minúsculas, sin espacios, palabras
  separadas con guiones medios (por ejemplo, `feat/websocket-alertas`).
- Prefijos permitidos:
  - `feat/` — nueva funcionalidad
  - `fix/` — corrección de bug
  - `refactor/` — cambios internos sin alterar comportamiento
  - `docs/` — documentación
  - `test/` — tests
  - `chore/` — mantenimiento (dependencias, config, CI)
  - `hotfix/` — corrección urgente en producción

## Commits
- Formato: `tipo: breve descripción del cambio` — en minúsculas y directo al grano,
  sin punto final (por ejemplo, `feat: añade canal websocket de alertas`).
- Tipos permitidos (alineados con los prefijos de rama):
  - `feat` — nueva funcionalidad
  - `fix` — corrección de bug
  - `refactor` — cambios internos sin alterar comportamiento
  - `docs` — documentación
  - `test` — tests
  - `chore` — mantenimiento (dependencias, config, CI)
  - `hotfix` — corrección urgente en producción
  - `style` — formato/estilo sin cambios de lógica (lint, espacios)
  - `perf` — mejoras de rendimiento
- Cada commit debe ser atómico: un único objetivo por commit. No mezcles cambios
  sin relación entre sí; sepáralos en commits distintos.

## Reglas
- Lee `specs/constitution.md` y la spec activa antes de tocar código.
- No te acredites como agente/IA en ninguna parte: ni en mensajes de commit
  (sin `Co-Authored-By` ni firmas), ni en descripciones de PR, ni en comentarios
  o partes visibles del código.
- Secretos: en desarrollo se usa `.env` local (gitignoreado) con valores de dev;
  en producción los secretos reales van cifrados con SOPS + age. Jamás commitear
  credenciales ni `.env`; solo archivos cifrados `*.enc.*` y el `.env.example`.
  No descifrar secretos de producción fuera del despliegue.
- Todo cambio de backend debe poder ejercitarse y reproducirse sin frontend:
  vía `pytest`, un management command (`manage.py …`), la API navegable de DRF
  o una llamada documentada (httpie/curl). Las tareas Celery y los canales
  WebSocket deben poder dispararse desde CLI para su verificación.
- No añadir dependencias nuevas ni servicios sin preguntar.
- Cualquier acción que requiera intervención humana (credenciales, claves, binarios,
  instalaciones locales, decisiones de infraestructura) se anota como checklist en
  `HUMAN_TODO.md` en vez de dejarla solo en la conversación.
- Respetar los límites de carpetas: no compartir código entre backend y frontend
  salvo por la API (DRF/WebSocket).
- Al terminar una feature, crea `specs/<feature>/resumen.md` con **qué se hizo** y **cómo un
  usuario corriente puede probarlo** (pasos concretos, ejecutables). Cuando algo de esa feature
  cambie, actualiza su resumen para que siempre refleje el estado real.
- Cada concepto que le genere dudas al usuario durante una feature se documenta en una sección
  **"Marco teórico"** de su `resumen.md`, explicado de forma accesible (qué es y por qué importa),
  para que quede como referencia reutilizable.

## Al terminar cualquier tarea
- Ejecutar los tests del área tocada (`pytest` y/o `pnpm --filter frontend test`).
- Pasar tipos (`mypy backend/`, `pnpm --filter frontend typecheck`).
- Pasar lint/formato (`ruff`/`black`, `eslint`/`prettier`, `cargo fmt`/`clippy`).
- Verificar que el entorno Docker sigue levantando sin errores.

### Rutas
- `HUMAN_TODO.md`: acciones pendientes que requieren intervención humana
- `specs/constitution.md`: principios del proyecto
- `specs/<feature>/spec.md`: requisitos de la feature
- `specs/<feature>/plan.md`: diseño técnico
- `specs/<feature>/tasks.md`: tareas de implementación
- `specs/<feature>/resumen.md`: resumen de qué se hizo, cómo probarlo y **marco teórico** de los conceptos que generaron dudas (se crea al terminar la feature; se actualiza con cada cambio)

`<feature>` es un nombre en kebab-case (por ejemplo, `login-con-google`).

### Identificadores
- `P-01` principios · `RF-001` requisitos funcionales · `S-01` supuestos · `C-01` hallazgos · `M-01` módulos · `D-01` decisiones · `T-001` tareas
- Los `RF` nunca se renumeran. Los eliminados se marcan `OBSOLETO`, no se borran.

### Estados
Cada artefacto tiene una línea `Estado:` al principio. Solo pasa a aprobado cuando el usuario lo aprueba de forma explícita.
- constitution.md: `borrador | aprobada`
- spec.md: `borrador | aprobada`
- plan.md: `borrador | aprobado`
- tasks.md: `borrador | aprobado`

### Configuración
- `sdd.max_principios`: 10
- `sdd.max_preguntas_spec`: 8
- `sdd.max_archivos_tarea`: 3
- `sdd.comando_tests`: pytest (backend) · `pnpm --filter frontend test` (frontend)
