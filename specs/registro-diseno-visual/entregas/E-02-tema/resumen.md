# Entrega E-02 · Tema guardado antes del primer pintado

Rama: `feat/registro-diseno-visual-tema` (apilada sobre `feat/registro-diseno-visual-barra-idioma`,
E-01) · PR: pendiente · Líneas de código y tests: 309 (límite: 400).

## Qué se hizo
- **Tema guardado y tema en uso** (`theme/theme.ts`, T-007): lee el tema elegido de
  `confiabilidad.theme` (y borra un valor no válido), lo guarda y lo aplica como `data-theme` en
  `<html>`. `useTheme` da el tema en uso: el elegido o, si no hay, el del sistema operativo, al que
  sigue cuando cambia. Con el almacenamiento bloqueado no falla.
- **Paleta oscura por elección o por sistema** (`styles/tokens.css`, T-008): la paleta oscura se
  aplica con `data-theme="dark"` o, sin elección, con el sistema en oscuro; elegir el claro gana
  aunque el sistema esté en oscuro.
- **Sin destello al cargar** (`index.html`, T-009): un script mínimo en la cabecera aplica el tema
  guardado antes de que cargue la aplicación, así nunca se ve el otro tema ni un instante.

El menú para elegir el tema llega en E-03; hasta entonces, el tema se elige a mano en el
almacenamiento del navegador.

## Tareas
El detalle de cada tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Tema guardado y tema en uso | `87f0ffa` |
| T-008 | Paleta oscura por elección o por sistema | `f72c9a6` |
| T-009 | Tema aplicado antes del primer pintado | `d7a4b09` |

## Cómo ejecutarlo y probarlo
Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver todos en verde (418). Levanta el frontend:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/register y, en las herramientas del navegador (F12), abre la consola y
ejecuta:
```js
localStorage.setItem("confiabilidad.theme", "dark")
```
Recarga: la página sale oscura desde el primer instante, sin destello claro. Prueba lo contrario con
`"light"` y el sistema operativo en oscuro: se queda clara. Para volver a seguir al sistema,
ejecuta:
```js
localStorage.removeItem("confiabilidad.theme")
```
Recarga y cambia el tema del sistema operativo: la página lo sigue.

## Marco teórico
- **Por qué un script en la cabecera y no en React.** El navegador pinta la página en cuanto tiene
  el HTML y el CSS; React tarda un poco más porque primero descarga y ejecuta la aplicación. Si el
  tema lo aplicara React, durante ese instante se vería el tema del sistema (el «destello»). Un
  script de pocas líneas en la cabecera se ejecuta antes del primer pintado y lo evita.
