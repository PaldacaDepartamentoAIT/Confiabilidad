# Entrega E-24 · Correcciones de la tercera validación

Rama: `feat/registro-flujo-tests-finales` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#57](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/57) ·
Líneas de código y tests: 35 (límite: 400).

La tercera validación de la feature (subagente sin contexto, 2026-11-05) dio NO CUMPLIDA sin fallos
de código: tres requisitos tenían una parte sin aserción. El comportamiento ya era correcto. El
usuario aprobó estas tres tareas, solo de tests.

## Qué se hizo
- **Contraseña al salir del campo** (`PasswordStep.test.tsx`, T-061): salir del campo de contraseña
  (y de su botón de mostrar) con `corta` muestra «Usa al menos 12 caracteres.» sin llamar al
  servidor (RF-013).
- **Identificador completado** (`test_registration_flow_api.py`, T-062): tras crear la cuenta,
  consultar, verificar, reenviar y completar con ese identificador dan `404 not_found` (RF-015).
- **Lo escrito se conserva tras un `429`** (`RegisterPage.test.tsx`, `VerifyPage.test.tsx`,
  `PasswordStep.test.tsx`, T-063): el formulario, el código y la contraseña siguen escritos al
  volver a permitir la acción (RF-024).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-061 | Validación de la contraseña al salir del campo | `5272a72` |
| T-062 | Un identificador completado da «no encontrado» | `60faf5a` |
| T-063 | El límite superado conserva lo escrito | `fa3edd2` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, ejecuta los tests de las pantallas del registro:
```bash
pnpm --filter frontend exec vitest run src/registration
```
Deberías ver todos en verde. Levanta Postgres y Redis:
```bash
docker compose -f docker/docker-compose.yml up -d db redis
```
Ejecuta los tests de la API del flujo:
```bash
docker compose -f docker/docker-compose.yml run --rm backend pytest -q apps/accounts/tests/test_registration_flow_api.py
```
Deberías ver todos en verde.

## Marco teórico
- **Un test que pasa desde el principio también vale, si mata un mutante.** Estas tareas fijan un
  comportamiento que ya existía. Su prueba no es la fase roja, sino que un cambio que rompa ese
  comportamiento (quitar la validación al salir, no borrar el registro, vaciar el formulario) haga
  fallar el test.
