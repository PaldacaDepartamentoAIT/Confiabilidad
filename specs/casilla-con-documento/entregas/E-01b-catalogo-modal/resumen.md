# Entrega E-01b · Catálogo: modal de ejemplo

Rama: `feat/casilla-con-documento-modal` (sale de `feat/casilla-con-documento`) · PR: [#105](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/105) ·
Líneas de código y tests: 83 (límite: 400).

## Qué se hizo
- El catálogo tiene una sección nueva, «Documento en un modal», con un botón «Abrir el documento». Al pulsarlo se
  abre el `DocumentModal` de E-01 con un documento de ejemplo (títulos, párrafos con énfasis, listas, un enlace
  y texto de relleno para que haga scroll) y, en el pie, una casilla «Acepto los términos».
- Se cierra con la «×», con Escape y con un clic en la cortina. Verificado en un navegador real a 1000 px en
  claro y a 420 px en oscuro: se abre, la caja mide 640 px (388 px a 420 px), el foco queda en la «×» y Escape
  lo cierra.
- Todavía no tiene su aspecto final: la etiqueta de la casilla del pie se lee mal (tinta sobre negro), los
  enlaces salen en el color principal y la cortina es la del navegador. Se arregla en E-02 (T-006).
- Esta parte salió de una entrega de 465 líneas, dividida en dos por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-005 | Catálogo: modal de ejemplo | `f02860a` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 59 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Documento en un modal», pulsa «Abrir el documento» y ciérralo con la
«×», con la tecla Escape y pulsando fuera de la caja.

## Marco teórico
- **Contenido de ejemplo:** el catálogo enseña cada pieza con textos inventados y en español, con su propio
  idioma, para no mezclarlos con los de la aplicación.
