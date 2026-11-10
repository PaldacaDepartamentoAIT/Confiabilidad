# Entrega E-09 · Menú lateral: cabecera y navegación

Rama: `feat/sistema-de-diseno-menu-lateral-base` · PR: [PaldacaDepartamentoAIT/Confiabilidad#83](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/83) ·
Líneas de código y tests: 329 (límite: 400).

## Qué se hizo
- Hay un menú lateral con la identidad nueva: fondo del color secundario, 232 px de ancho y una
  línea de 1 px a su derecha. Tiene una cabecera de 64 px con el nombre del sistema (en negrita y
  subrayado, que sigue el idioma) y una navegación con los elementos que se le pasan como datos:
  cada uno con su icono y su etiqueta, en filas de 36 px. El elemento de la página actual se marca
  con una línea de 2 px bajo él, y los que tengan un contador lo muestran a la derecha.
- Para el lector de pantalla, el menú es una zona llamada «Menú principal» y su navegación,
  «Secciones», en los tres idiomas. El elemento actual lleva `aria-current="page"`.
- La página de muestra tiene una sección nueva, «Menú lateral», con el menú dentro de un marco de
  440 px de alto, en claro y oscuro.
- Lo que falta de este menú llega en E-09b: contraerlo y expandirlo con su botón, y el pie con los
  botones de tema, de idioma y del usuario. La entrega del menú medía 594 líneas y, por el límite
  de 400, se dividió por la regla de `AGENTS.md`; las tareas T-060 y T-061 nacieron de esa división.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-059 | Textos del menú lateral en tres idiomas | `3978b2e` |
| T-029 | Menú lateral: cabecera y navegación | `c25b0bd` |
| T-030 | Catálogo: menú lateral | `c25b0bd` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 44 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Menú lateral» y comprueba el menú: cabecera con el nombre,
cuatro secciones con icono, «Activos» marcada con una línea y un contador en «Alarmas». Pulsa el
botón de tema de la barra para verlo en claro y oscuro.

## Marco teórico
- **Elemento actual (`aria-current="page"`):** además de la línea visual, la sección en la que estás
  se marca para el lector de pantalla, que la anuncia como «página actual».
- **Menú como datos:** el menú no sabe qué secciones existen; recibe una lista (icono, etiqueta,
  destino y contador). Así cada pantalla de la aplicación puede pasarle las suyas sin tocar el menú.
