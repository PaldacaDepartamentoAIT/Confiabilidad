# Entrega E-01 · Paleta Pizarra

Rama: `feat/sistema-de-diseno-paleta` · PR: [PaldacaDepartamentoAIT/Confiabilidad#66](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/66) ·
Líneas de código y tests: 352 (límite: 400).

## Qué se hizo
- La aplicación usa la paleta Pizarra de `docs/identidad-visual.md` en lugar de Niebla marina: claro
  por defecto y oscuro cuando el sistema operativo lo pide.
- Los colores tienen los mismos nombres que las pantallas de referencia (`--bg`, `--ink`, `--text2`,
  `--gray`, `--grid`, `--ctrl`, `--primary`, `--secondary`, `--p1`, `--p2`, `--warn`…), de modo que
  el CSS de las referencias se podrá reutilizar sin cambios.
- Queda preparado el tema fijado por el usuario: el atributo `data-theme="dark"` o `"light"` en
  `<html>` manda sobre el sistema operativo. Aún no hay botón que lo cambie (llega en E-02).
- Las reglas generales (fuente Manrope a 14 px, foco visible de 2 px en el color principal,
  movimiento reducido) viven en `base.css`. Las reglas de elementos sueltos de las piezas existentes
  se mantienen de forma transitoria con los colores nuevos, hasta que cada pieza se restilice.
- Un test compara cada color con las tablas de la guía en ambos temas y comprueba esas reglas.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Tokens v2 y base transitoria | `80fa7b2` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 30 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y cambia el tema claro/oscuro de tu sistema operativo: la página de
muestra debe pasar de fondo casi blanco a casi negro, con el azul grisáceo como color de los botones.

## Marco teórico
- **Variable CSS (token):** un nombre para un valor (`--ink` es el color del texto). Cambiar el valor
  en un solo sitio cambia todo lo que lo usa, y es lo que permite tener dos temas con el mismo CSS.
- **`prefers-color-scheme`:** el navegador informa de si el sistema operativo está en claro u
  oscuro. Con `data-theme` en `<html>` el usuario puede fijar el tema por encima de esa señal.
