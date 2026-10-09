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
- Backend: `cd backend && mypy .`  (modo estricto; la configuración está en `backend/pyproject.toml`)
- Frontend/Desktop: `pnpm --filter frontend typecheck`  (`tsc --noEmit`, modo strict)

Lint / formato:
- Backend: `cd backend && ruff check . && black .` (desde `backend/`, como el CI)
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
- Los mensajes de error y los textos que el código devuelve (por ejemplo, en `ValidationError`
  o en excepciones) se escriben en inglés, marcados para traducción con `gettext_lazy`.
- Estructura y código limpios: cada carpeta (backend / frontend / desktop) es
  independiente y no invade a las demás.
- Comandos para ejecutar: en cualquier texto (resúmenes, `HUMAN_TODO.md`, `README.md`,
  descripciones de PR y mensajes al usuario), cada comando que alguien deba ejecutar va en su
  propio bloque de código (```` ```bash ````), separado del texto, completo y listo para copiar y
  pegar.
  - Sin abreviaturas ni alias definidos en el texto (nada de `M`, `C` o `R`).
  - Sin el resultado esperado dentro del bloque ni explicaciones en la misma línea: el resultado
    va fuera, en la frase siguiente («Deberías ver…»).
  - Un valor que solo se conoce al ejecutar un paso anterior se escribe en mayúsculas entre
    ángulos (`<PUBLIC_ID>`), y la frase anterior al bloque dice de dónde sale.
  - Mencionar un comando dentro de una frase, sin pedir que se ejecute, no lo convierte en uno
    para copiar.

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
  - `spike/` — investigación técnica acotada que responde una pregunta; el entregable es
    una decisión escrita, no una funcionalidad
  - `poc/` — prototipo mínimo que demuestra que un enfoque ya elegido funciona de extremo
    a extremo

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
  - `spike` — investigación técnica acotada (ver prefijo `spike/`)
  - `poc` — prototipo mínimo de un enfoque ya elegido (ver prefijo `poc/`)
- Cada commit debe ser atómico: un único objetivo por commit. No mezcles cambios
  sin relación entre sí; sepáralos en commits distintos.
- Al trabajar desde la versión web (sesión remota), cada commit se sube al remoto justo
  después de hacerlo (`git push -u origin <rama>`): el entorno es efímero y lo que no se
  sube se pierde al cerrarse la sesión. Si el push falla, se anota en `HUMAN_TODO.md`.

## Reglas
- Lee `specs/constitution.md` y la spec activa antes de tocar código.
- Al hablar con el usuario, cada identificador (`T-002`, `RF-005`, `D-03`, `S-06`, `C-01`,
  `M-02`, `CF-1`, `P-04`…) va acompañado de su título o de una descripción breve la primera vez
  que aparece en cada mensaje; por ejemplo: «T-002 (código, identificador público y huella)».
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
- **Modos de aprobación.** Cada feature declara el suyo en `spec.md`, justo debajo de `Estado:`,
  con la línea `Aprobación: fuerte | ligera`. `sdd-spec` lo pregunta antes de la entrevista; los
  demás agentes y sesiones leen esa línea y la respetan sin volver a preguntar. Si falta, el modo
  es fuerte. Solo cambia si el usuario lo pide de forma explícita, y el cambio se anota en el
  historial de la spec.
  - **Modo fuerte.** Aprobar una idea o decisión **no** aprueba su **redacción**. Antes de aplicar
    cualquier cambio de texto o código (spec, plan, tareas, resumen, documentación o código),
    preséntalo al usuario y ofrécele dos opciones: **Aceptar** o **Rechazar**. Si lo rechaza,
    permítele introducir una corrección y vuelve a presentar la versión corregida. **No continúes
    con el flujo de trabajo hasta que el usuario apruebe explícitamente.** Se implementa una tarea
    cada vez y se detiene tras cada una.
  - **Modo ligero.** Siguen necesitando aprobación explícita, y nunca se aprueban solos: la spec
    (tras `sdd-clarificar`), el plan, la lista de tareas y cualquier cambio en ellos (`sdd-cambio`
    con su análisis de impacto, y toda tarea nueva, sea por un bug, un mutante o la validación).
    Todo lo demás es automático: `sdd-implementar` encadena las tareas sin pedir aprobación de cada
    diff, y al terminarlas se lanza `sdd-validar`. Los textos que se escriben sin Aceptar/Rechazar
    (`resumen.md`, `HUMAN_TODO.md`, las marcas y decisiones de `tasks.md`, la entrada de validación)
    se listan en el informe final. El código se revisa en el PR, que solo se abre si el usuario lo
    confirma. Paradas obligatorias (detente y pregunta; resuelta la parada, la cadena sigue en modo
    ligero sin volver a preguntar):
    - ambigüedad o contradicción en la spec;
    - una decisión de seguridad o de diseño que la spec o el plan no cubren;
    - una desviación del plan o la necesidad de tocar un módulo fuera de su alcance;
    - superar `sdd.max_archivos_tarea` sin una `Excepción:` en la tarea;
    - añadir dependencias, servicios o infraestructura;
    - un mutante que sobrevive sin un arreglo claro: un test dentro de los archivos de la tarea que
      lo mate sin afirmar nada que no esté en la spec o el plan. Un mutante equivalente se anota en
      el informe y no detiene;
    - un veredicto de validación distinto de CUMPLIDA: las tareas de corrección y el cierre con
      riesgo residual los decide el usuario.
  - **Qué se muestra al pedir una aprobación (en ambos modos).** No se pide aprobar nada que el
    usuario no haya visto. Antes de cada aprobación, el texto completo que se aprueba (o, si se
    modifica algo existente, cada cambio con su versión anterior y la nueva) va **en el propio
    mensaje** de la conversación: no basta con un archivo adjunto, la salida de una herramienta ni
    un resumen. Si es demasiado largo para un mensaje, se divide en partes y se aprueba parte por
    parte. Un resumen puede acompañar al texto, nunca sustituirlo. Si el usuario dice que no ha
    visto lo que se le pide aprobar, esa aprobación no cuenta: se vuelve a mostrar y se vuelve a
    preguntar. La pregunta de aprobación se hace en ese mismo mensaje, como texto final, y no con
    una ventana de opciones que pueda ocultar lo que hay que aprobar.
  - **En ambos modos** se mantienen las reglas de ramas y commits, no acreditarse como IA,
    `HUMAN_TODO.md`, el `resumen.md` con marco teórico, el test de mutación de cada tarea y que la
    validación la haga un subagente sin contexto de la implementación (o una sesión nueva si el
    entorno no admite subagentes; nunca la misma sesión).

## Al terminar cualquier tarea
- Ejecutar los tests del área tocada (`pytest` y/o `pnpm --filter frontend test`).
- Pasar tipos (`cd backend && mypy .`, `pnpm --filter frontend typecheck`).
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
