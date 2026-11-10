# Entrega E-07c · Selector nativo en táctiles y selector propio en el registro

Rama: `feat/sistema-de-diseno-selector-tactil` · PR: pendiente ·
Líneas de código y tests: 360 (límite: 400).

## Qué se hizo
- Los selectores de la aplicación (por ejemplo, el país del registro) usan ahora el selector propio
  cuando el puntero principal es fino (ratón o lápiz) y el `<select>` nativo del sistema cuando es
  táctil, con la misma etiqueta, opciones, ayuda y error. Si la página se abre en un dispositivo
  que cambia de puntero (por ejemplo, una tablet con ratón conectado), cambia de uno a otro sin
  recargar. Si el navegador no sabe decir el tipo de puntero, se usa el nativo, que funciona en
  cualquier sitio.
- El `<select>` nativo toma el aspecto de campo de la guía (etiqueta, 36 px de alto, ayuda y error con
  icono) y ocupa todo el ancho de su contenedor.
- El formulario de registro valida el país igual con el selector propio: ahora sabe leer el valor
  de un botón con `name` y `value`, no solo de un campo o un `<select>`.
- Verificado en un navegador real con la API simulada: con puntero fino el país es un botón del
  ancho de su contenedor y elegir «Chile» guarda su valor; con puntero táctil es un `<select>`
  del ancho de su contenedor.
- Los tests de registro y de los demás formularios no cambian: el entorno de test (jsdom) no sabe el
  tipo de puntero y usa el nativo, como hasta ahora.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-022 | Detección de puntero táctil | `436bf75` |
| T-024 | Selector nativo en dispositivos táctiles | `fadcc9e` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 42 archivos de test en verde.

Levanta la aplicación con el backend (la página de registro carga los países de la API):
```bash
docker compose -f docker/docker-compose.yml up
```
Abre http://localhost:5173/register: el campo «País» debe ser un botón que abre una lista. En las
herramientas de desarrollo del navegador, activa la emulación de un dispositivo móvil, recarga y
comprueba que ahora es el selector nativo del sistema.

## Marco teórico
- **Puntero fino y grueso (`pointer: coarse`):** el navegador distingue si el dispositivo de
  entrada principal es preciso (ratón) o impreciso (dedo). En móvil, la lista nativa del sistema es
  más cómoda y más accesible que una propia, por eso se conserva allí.
- **Reserva segura:** si el navegador no sabe decir el tipo de puntero, se elige el control nativo
  porque es el que mejor funciona en cualquier circunstancia.
