# Entrega E-01 · Componente de modal de documento

Rama: `feat/casilla-con-documento-componente-modal` (sale de `feat/casilla-con-documento`) · PR: [#104](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/104) ·
Líneas de código y tests: 382 (límite: 400).

## Qué se hizo
- Hay un componente `DocumentModal`, sin usar todavía en pantallas (se ve en el catálogo en E-01b). Abierto,
  pinta un diálogo nativo (`<dialog>`) fuera del formulario, con tres partes en este orden: un botón «×»
  arriba, el documento en Markdown con desplazamiento y un pie para lo que reciba (la casilla, más adelante).
  Cerrado, no pinta nada.
- El diálogo tiene nombre accesible (sin título visible). Los enlaces del documento se abren en una pestaña
  nueva y el contenido con desplazamiento se alcanza con el teclado.
- Se cierra con la «×», con Escape y con un clic en la cortina; un clic dentro de la caja no lo cierra. Es un
  componente controlado: solo avisa de que se quiere cerrar y quien lo usa decide.
- El texto del botón de cerrar existe en español («Cerrar»), portugués («Fechar») e inglés («Close»).
- Los tests de jsdom disponen de un doble de `showModal()` y `close()`, porque jsdom no los implementa; el
  comportamiento real del navegador (foco atrapado, página de detrás inerte) se comprueba en Chromium en E-02.
- Esta parte salió de una entrega de 465 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Doble de `<dialog>` para los tests de jsdom | `969a802` |
| T-002 | Texto de «Cerrar» del modal en tres idiomas | `0059a53` |
| T-003 | Modal: estructura, documento y nombre accesible | `6710ce3` |
| T-004 | Modal: cierre por «×», Escape y cortina | `a950240` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 59 archivos de test en verde, entre ellos `DocumentModal.test.tsx` (14 tests) y
`dialogStub.test.ts` (4 tests).

## Marco teórico
- **`<dialog>` nativo y modal:** cuando se abre con `showModal()`, el navegador deja inerte el resto de la
  página, atrapa el foco dentro del diálogo y atiende la tecla Escape sin que haya que programarlo. Es más
  fiable que hacerlo a mano.
- **Componente controlado:** el modal no decide cuándo cerrarse; avisa («quiero cerrarme») y quien lo usa
  cambia `open`. Así el estado vive en un solo sitio.
- **Cortina:** la capa oscura de detrás. Aquí el diálogo ocupa toda la pantalla y la caja va dentro, de modo
  que un clic sobre el propio diálogo es un clic fuera de la caja.
