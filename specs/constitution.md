# Constitución
Estado: aprobada

## P-01 Secretos siempre cifrados
Las variables de entorno y credenciales de producción se versionan cifradas con SOPS + age; nunca en texto claro.
Se verifica: no existen archivos `.env` ni secretos en claro en el repo, solo archivos `*.enc.*`; revisión con `git grep` de patrones sensibles y `sops --decrypt` funcional sobre los cifrados.

## P-02 Entorno reproducible con Docker
Cualquier desarrollador levanta backend, frontend y servicios (Redis, BD, Celery) con un solo comando de Docker desde un clon limpio.
Se verifica: `git clone` limpio + `docker compose -f docker/docker-compose.yml up` arranca todos los servicios sin pasos manuales adicionales.

## P-03 Backend verificable desde CLI
Todo cambio de backend puede ejercitarse y reproducirse sin frontend (pytest, management command, API navegable de DRF o httpie/curl); las tareas Celery y los canales WebSocket se pueden disparar desde CLI.
Se verifica: cada feature de backend aporta al menos una vía CLI documentada (test, `manage.py …` o llamada httpie) en su `plan.md`/`tasks.md`.

## P-04 TDD estricto
Toda funcionalidad se desarrolla escribiendo primero un test que falla, luego la implementación mínima, y finalmente la suite en verde.
Se verifica: la revisión de commits/PR muestra el test antes o junto a la implementación; la suite (`pytest`, `pnpm --filter frontend test`) pasa en CI.

## P-05 Cobertura de líneas ≥ 80%
El código nuevo mantiene una cobertura de líneas de al menos el 80% en backend y frontend.
Se verifica: informe de `pytest --cov` y de Vitest `--coverage` con umbral ≥ 80% que bloquea en CI.

## P-06 Análisis estático limpio
Todo el código pasa lint y formato sin errores ni warnings.
Se verifica: `ruff check .`, `black --check .`, `pnpm lint` (ESLint), `pnpm format --check` (Prettier) y `cargo fmt --check` + `cargo clippy` sin avisos en CI.

## P-07 Tipado estático en todo el stack
El código está tipado y pasa el análisis de tipos sin errores, tanto en backend (Python) como en frontend/desktop (TypeScript).
Se verifica: `mypy` en modo estricto sin errores sobre `backend/`, y `tsc --noEmit` sin errores con TypeScript en modo `strict` sobre `frontend/` (y `desktop/`) en CI.

## P-08 Separación de capas
Backend, frontend y desktop son independientes; se comunican solo por la API (DRF/WebSocket), y el desktop (Tauri) reutiliza el frontend web sin duplicar código React.
Se verifica: no hay imports cruzados entre `backend/` y `frontend/`; `desktop/` no contiene componentes React propios (solo el shell Tauri que carga `frontend/`); revisión de la estructura de carpetas.

## P-09 Idioma y convención de código
El código se escribe en inglés según la convención de cada lenguaje; los comentarios van en español y solo cuando son imprescindibles.
Se verifica: revisión de PR; identificadores en inglés (PEP 8 / camelCase / snake_case Rust) y ausencia de comentarios triviales.

## P-10 Convención de ramas, commits y sin atribución de IA
Las ramas siguen `tipo/descripcion-corta` y los commits `tipo: descripción`; ningún commit, PR o parte visible del código acredita a un agente/IA.
Se verifica: revisión de nombres de rama y mensajes de commit contra los prefijos permitidos; ausencia de trailers `Co-Authored-By` o firmas de IA.
