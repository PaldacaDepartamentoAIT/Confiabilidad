# Entrega E-10b · Panel superpuesto del menú en pantallas pequeñas

Rama: `feat/sistema-de-diseno-con-sesion-panel` (sale de `feat/sistema-de-diseno-con-sesion-base`) · PR: pendiente ·
Líneas de código y tests: 358 (límite: 400).

## Qué se hizo
- En pantallas de menos de 768 px, el menú lateral deja de ocupar sitio y pasa a ser un panel
  superpuesto, de 232 px, que entra desde la izquierda con una animación de 0,25 s, **sin velo**
  detrás. Cerrado, queda oculto del teclado y del lector de pantalla; abierto, el foco pasa a su
  botón de la cabecera, que ahora se llama «Cerrar menú».
- El panel se cierra con ese botón o con Escape (devolviendo el foco al botón que lo abrió), con un
  clic fuera de él o al elegir un elemento del menú, y también si la pantalla se ensancha mientras
  está abierto. En pantallas pequeñas no existe el estado contraído. El botón que abre el panel
  (el que lo señale con `aria-controls`) no cuenta como «fuera».
- Hay un hook, `useMediaQuery`, para lo que cambia el comportamiento según el tamaño de pantalla (el
  aspecto lo decide el CSS), y dos textos nuevos, «Abrir menú» y «Cerrar menú», en los tres idiomas.
- Se corrigió la spec: RF-009 decía «con un velo detrás», pero la guía y las referencias dicen «sin
  velo»; decidiste que valía la guía y se aprobó el cambio de texto (queda anotado en su historial).
- El botón de la barra que abre el panel llega en E-10c: hasta entonces, el panel no se puede abrir
  en la aplicación, solo en los tests. Por eso esta entrega no se ve por sí sola.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-031 | `useMediaQuery` | `2e4d60d` |
| T-062 | Textos del panel móvil del menú en tres idiomas | `05e4507` |
| T-032 | Panel superpuesto del menú | `aebd5c4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 46 archivos de test en verde, entre ellos `src/layouts/Sidebar.test.tsx` (con los tests
del panel) y `src/layouts/useMediaQuery.test.ts`.

## Marco teórico
- **Panel superpuesto frente a menú fijo:** en pantallas anchas el menú ocupa su columna; en las
  estrechas no hay sitio, así que se esconde y se abre encima del contenido. El CSS decide cómo se
  ve y el hook solo decide lo que cambia el comportamiento (foco, cierre y ocultación al lector).
- **Devolver el foco:** al cerrar el panel con el teclado, el foco vuelve al botón que lo abrió, para
  que quien navega con teclado no se pierda en la página.
