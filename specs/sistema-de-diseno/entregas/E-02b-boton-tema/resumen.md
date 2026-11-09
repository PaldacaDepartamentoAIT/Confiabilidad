# Entrega E-02b · Botón de tema

Rama: `feat/sistema-de-diseno-boton-tema` (sale de `feat/sistema-de-diseno-modulo-tema`) · PR: pendiente ·
Líneas de código y tests: 263 (límite: 400).

## Qué se hizo
- La página de muestra tiene un botón de tema, bajo el selector de idioma. Muestra el tema activo
  («Claro» u «Oscuro») con un icono de sol o luna; al pulsarlo con el ratón o con el teclado
  (Intro o Espacio) alterna entre claro y oscuro con una transición suave de 0,4 s.
- La elección se recuerda: al recargar la página se mantiene, por encima del tema del sistema
  operativo. Un valor guardado que no sea válido se ignora y se borra.
- El lector de pantalla anuncia el tema nuevo, y el nombre accesible del botón dice el tema actual y
  la acción («Tema claro. Cambiar tema»), en los tres idiomas.
- El tema se aplica al arrancar la aplicación, antes de dibujar nada, para que no parpadee el tema
  equivocado.
- Provisional: el botón ocupa todo el ancho porque la página de muestra aún no tiene barra superior
  ni menú; su sitio definitivo llega con el diseño público y el menú lateral.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-004 | Botón de tema | `61f810d` |
| T-005 | Aplicar el tema al arrancar y mostrar el botón | `a9d7d39` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 32 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, pulsa el botón de tema (debe pasar de fondo casi blanco a casi negro),
recarga la página y comprueba que se conserva.

## Marco teórico
- **Región viva (`aria-live`):** zona de la página que el lector de pantalla lee cuando cambia su
  texto. El botón la usa para decir «Tema oscuro» sin mover el foco.
- **Aplicar antes de renderizar:** si el tema se aplicara después de dibujar la página, se vería un
  instante el tema equivocado. Por eso se fija en `main.tsx`, antes de crear la interfaz.
