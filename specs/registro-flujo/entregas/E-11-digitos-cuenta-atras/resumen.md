# Entrega E-11 · Contraseña como el servidor y cuenta atrás

Rama: `feat/registro-flujo-digitos-cuenta-atras` · PR: pendiente ·
Líneas de código y tests: 197 (límite: 400).

## Qué se hizo
- **Dígitos como el servidor** (`frontend/src/forms/digits.ts`, `passwordRules.ts`): la regla «no
  uses solo números» del navegador cuenta como dígito lo mismo que `str.isdigit()` del servidor.
  Antes solo contaba los dígitos decimales (`\p{Nd}`) y aceptaba `²²²²²²²²²²²²`, que el servidor
  rechaza. Ahora suma la lista de superíndices, subíndices, dígitos rodeados y similares, generada
  con `unicodedata` de Python 3.12 (la versión del backend), con el comando en un comentario. Un test
  recorre la tabla «Casos compartidos de contraseña» de la spec, la misma que recorre el backend.
- **Cuenta atrás** (`frontend/src/registration/useCountdown.ts`): un hook que cuenta hacia atrás
  desde los segundos que dé el servidor, avisa al llegar a cero y se reinicia con un valor nuevo.
  Lo usarán la caducidad del código, el reenvío y las esperas por límite superado (desde E-12).
- **Cambio de E-10, hecho después de su PR**: el test de axe de la casilla y el selector excluye de
  forma explícita la regla de contraste, que en jsdom no se puede medir (ver el resumen de E-10).

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-039 | Dígitos como el servidor | `7a01f5b` |
| T-040 | Cuenta atrás | `c8d1c20` |
| — | Contraste excluido en el test de axe de E-10 | `ea4a184` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```
Ejecuta los tests de las reglas de contraseña:
```bash
pnpm --filter frontend exec vitest run src/forms/passwordRules
```
Deberías ver 22 tests en verde, entre ellos los 8 casos compartidos con el backend. Ejecuta los
tests de la cuenta atrás:
```bash
pnpm --filter frontend exec vitest run src/registration/useCountdown
```
Deberías ver 7 tests en verde. Arranca el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y escribe `²²²²²²²²²²²²` en «Nueva contraseña»; al salir del campo
deberías ver «No uses solo números.». Antes de esta entrega, el navegador lo aceptaba.

## Marco teórico
- **Qué es un dígito depende de a quién preguntes.** Unicode clasifica los caracteres numéricos en
  tipos. Los dígitos decimales normales (`0`–`9`, los arábigos `٠`–`٩`…) son `Nd`. Los superíndices
  (`²`), los subíndices (`₂`) o los rodeados (`②`) son otro tipo, `Numeric_Type=Digit`. Python, con
  `str.isdigit()`, acepta los dos tipos; JavaScript solo sabe preguntar por `Nd`. Por eso hace falta
  la lista explícita.
- **La versión de Unicode también importa.** Cada año Unicode añade escrituras. El navegador puede
  conocer una versión más nueva que el Python del servidor: hoy hay 80 dígitos de escrituras
  añadidas en Unicode 16 que el navegador cuenta como dígitos y el servidor no. Solo afecta a una
  contraseña hecha únicamente de esos caracteres, que el navegador rechazaría de más; es un riesgo
  residual aceptado que desaparece al actualizar Python en el backend.
- **Contar contra la hora, no contar ticks.** Los navegadores ralentizan los temporizadores de las
  pestañas en segundo plano. Si la cuenta atrás restara uno en cada tick, al volver mostraría más
  tiempo del que queda. Guardar la hora límite y calcular lo que falta en cada tick lo evita.
