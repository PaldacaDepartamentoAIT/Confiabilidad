# Entrega E-06 · Cliente de autenticación y almacenamiento de token para escritorio

Rama: `feat/inicio-cierre-sesion-cliente-auth` · PR: pendiente · Líneas de código y tests: 333 (límite: 400).

## Qué se hizo
- Se creó `frontend/src/auth/tokenStorage.ts` (`TokenStorage`, `createTokenStorage`, `tokenStorage`) para guardar, leer y limpiar el `session_token` del cliente de escritorio en `localStorage` con respaldo en memoria si el almacenamiento falla (`T-014`, `RF-006`, `RF-018`, `S-07`).
- Se amplió `frontend/src/api/client.ts` y su suite `frontend/src/api/client.test.ts` (`T-014`, `RF-011`, `RF-018`):
  - En modo `app`, adjunta `X-Session-Token` cuando hay token guardado.
  - Interpreta HTTP `401` como `{ kind: "unauthenticated" }` y HTTP `403` con `code: "terms_required"` como `{ kind: "termsRequired", termsStatus }`, manteniendo intactas las respuestas existentes.
- Se crearon `frontend/src/api/auth.ts` y `frontend/src/api/auth.test.ts` con `getSession`, `login` (guarda `session_token` cuando viene en la respuesta), `logout` (borra siempre el token local en `finally` aunque el servidor responda `401` o falle la red), `acceptTerms`, `listSessions`, `revokeSession` y `revokeOtherSessions` (`T-015`, `RF-001`, `RF-006`, `RF-008`, `RF-009`, `RF-012`, `RF-018`).
- Se dividieron `T-016` y `T-017` en `E-06b` (`feat/inicio-cierre-sesion-textos-auth`) para mantener cada PR por debajo de 400 líneas.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-014 | Almacenamiento de token para escritorio y soporte de autenticación en el cliente API | `5ee7464` |
| T-015 | Llamadas de la API de autenticación y sesiones | `1b9472f` |

## Cómo ejecutarlo y probarlo
Actualiza las ramas remotas y cambia a la rama de la entrega:

```bash
git fetch origin
```

```bash
git checkout feat/inicio-cierre-sesion-cliente-auth
```
Deberías ver tu copia de trabajo en `feat/inicio-cierre-sesion-cliente-auth`.

Ejecuta los tests de esta entrega con Vitest:

```bash
pnpm --filter frontend test src/api/client.test.ts src/api/auth.test.ts
```
Deberías ver los 2 archivos de tests (25 tests en total) en verde.

Ejecuta el linter, formato y chequeo de tipos del frontend:

```bash
pnpm --filter frontend lint
```
Deberías ver la salida limpia sin errores.

```bash
pnpm --filter frontend typecheck
```
Deberías ver `tsc --noEmit` terminar sin errores.
