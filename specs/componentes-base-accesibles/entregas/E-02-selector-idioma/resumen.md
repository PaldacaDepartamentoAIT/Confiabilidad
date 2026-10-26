# Entrega E-02 · Selector de idioma que recuerda la elección

Rama: `feat/componentes-base-accesibles-selector-idioma`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#22](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/22) ·
Líneas de código y tests: 279 (límite: 400).

## Qué se hizo
- La página tiene un selector de idioma: un grupo llamado «Idioma» (o «Language») con tres
  botones, «Español», «Português (Brasil)» y «English», cada uno escrito en su propio idioma y
  marcado con él, para que el lector de pantalla lo pronuncie bien.
- El botón del idioma activo se anuncia como «presionado». El idioma solo cambia al activar un
  botón con Enter, Espacio o clic, nunca al recorrerlos con Tab.
- Al cambiar de idioma, toda la página, el idioma del documento y el título de la pestaña cambian
  sin recargar, y el foco se queda en el botón pulsado.
- La elección se guarda en el navegador y manda sobre el idioma del navegador en las siguientes
  visitas. Si lo guardado no es `es`, `pt-BR` ni `en`, se borra y se vuelve al idioma del
  navegador. Si el navegador bloquea el almacenamiento, el selector funciona igual durante la
  visita, pero la elección no se recuerda.
- Dependencia nueva de desarrollo: `@testing-library/user-event`, para simular el teclado en los
  tests.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-007 | Idioma elegido guardado en el navegador | `0984db0` |
| T-008 | Selector de idioma | `a5f094c` |
| T-009 | Selector de idioma en la aplicación | `c573e22` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 40 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173, con el selector de idioma encima del encabezado.

Pruébalo solo con el teclado:
1. Haz clic en la barra de direcciones y pulsa Tab hasta llegar a «Português (Brasil)». Deberías
   ver que el idioma aún no cambia al pasar por los botones.
2. Pulsa Enter. Deberías ver el encabezado «Confiabilidade», la pestaña «Confiabilidade —
   Componentes» y el foco todavía en «Português (Brasil)».
3. Pulsa Tab una vez para llegar a «English» y luego Espacio. Deberías ver la página en inglés.
4. Recarga la página. Deberías verla todavía en inglés, aunque tu navegador esté en otro idioma.

Para volver a empezar como un visitante nuevo, en DevTools (F12) → **Application** → **Local
storage** → `http://localhost:5173`, borra la clave `confiabilidad.language` y recarga.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Fuera de esta entrega
El selector no tiene aún estilo propio (se ve con el aspecto por defecto del navegador), y la
página todavía no tiene campos ni formulario: llegan a partir de E-03.
