# Entrega E-07 · Escritura para saltar a una opción en los menús

Rama: `feat/sistema-de-diseno-escritura-menu` · PR: pendiente ·
Líneas de código y tests: 186 (límite: 400).

## Qué se hizo
- En los menús desplegables, escribir una o varias letras salta a la siguiente opción cuyo texto
  empieza por ellas, sin distinguir mayúsculas. Funciona con el menú abierto y también cerrado (lo
  abre en la opción encontrada). Repetir la misma letra recorre las opciones que empiezan por ella y
  vuelve al principio al llegar al final. Una pausa de 0,7 s olvida lo escrito, y las combinaciones
  con Ctrl, Alt o Meta no cuentan como texto, para no estorbar a los atajos del navegador.
- Esto vale ya para el botón de idioma y el menú de plantas de la página de muestra, y valdrá para el
  selector propio y el selector de pestañas que llegan después.
- Esta parte salió de la entrega del selector propio, que medía 594 líneas; por la regla de
  `AGENTS.md` se dividió en tres entregas (esta, E-07b y E-07c).

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-058 | Escritura para saltar a una opción en el menú | `85c70cc` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 41 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Menú e idioma», llega con Tab al menú de plantas y escribe
«s» (salta a «Sur») o «e» (salta a «Este»); pulsa Intro para elegirla.

## Marco teórico
- **Búsqueda por escritura (type-ahead):** en una lista desplegable, el teclado permite saltar a una
  opción escribiendo su principio, como en una lista nativa. Las letras escritas seguidas forman un
  prefijo; si se espera, el prefijo se olvida y empieza uno nuevo.
