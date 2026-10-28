# Entrega E-01 · Interfaz traducida según el idioma del navegador

Rama: `feat/componentes-base-accesibles-traduccion` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#20](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/20) ·
Líneas de código y tests: 416 (límite con la excepción aprobada: 500).

## Qué se hizo
- La aplicación tiene sus textos en español, portugués de Brasil e inglés. Son provisionales y
  están escritos para el contexto real (cuenta de usuario de una herramienta de gestión de activos
  industriales). Los de toda la feature ya están escritos, aunque la página aún solo usa el
  encabezado y la introducción.
- Al abrir la página, el idioma sale del navegador: cualquier variante de español → español, de
  portugués → portugués de Brasil, de inglés → inglés. Si el navegador no prefiere ninguno de los
  tres, la página sale en inglés.
- Si a un idioma le falta un texto o lo tiene vacío, se muestra el inglés, nunca la clave interna.
- El idioma del documento (`<html lang>`, que el lector de pantalla usa para elegir la voz) y el
  título de la pestaña siguen al idioma activo.
- Las traducciones se vigilan dos veces: el compilador rechaza una clave que no existe o un idioma
  al que le falta o le sobra una clave, y un test falla si algún texto está vacío.
- Dependencias nuevas: `i18next` y `react-i18next`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-001 | Textos provisionales de toda la feature en tres idiomas | `3633e19` |
| T-002 | Instancia de traducción con reserva en inglés | `b4d9b0f` |
| T-003 | Claves de traducción comprobadas por el compilador | `971020d` |
| T-004 | Idioma inicial según el navegador | `5b7d383` |
| T-005 | Idioma y título del documento sincronizados | `534781b` |
| T-006 | Aplicación traducida al arrancar | `2b74357` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 30 tests en verde.

Comprueba los tipos, que es donde se detecta una clave de traducción que no existe:
```bash
pnpm --filter frontend typecheck
```
Deberías ver que termina sin errores.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173, con el encabezado en el idioma de tu navegador.

Para probar otros idiomas sin cambiar la configuración del sistema, en Chrome abre DevTools
(F12) → menú de tres puntos → **More tools** → **Sensors** y, en **Location**, cambia **Locale**:

| Locale | Encabezado | Título de la pestaña |
|---|---|---|
| `pt-BR` | Confiabilidade | Confiabilidade — Componentes |
| `en-US` | Reliability | Reliability — Components |
| `fr-FR` | Reliability | Reliability — Components |
| `es-AR` | Confiabilidad | Confiabilidad — Componentes |

Recarga la página tras cada cambio. Para ver el idioma del documento, inspecciona la etiqueta
`<html>`: su atributo `lang` debe ser `pt-BR`, `en` o `es`.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Comprobado por el usuario en local el 2026-10-28.

## Fuera de esta entrega
Todavía no hay selector de idioma: el idioma solo cambia con el del navegador. Llega en E-02.
