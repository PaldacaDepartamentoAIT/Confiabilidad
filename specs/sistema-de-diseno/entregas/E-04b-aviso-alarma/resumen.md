# Entrega E-04b · Aviso de alarma y sección de botones y avisos

Rama: `feat/sistema-de-diseno-aviso-alarma` (sale de `feat/sistema-de-diseno-boton-aviso`) · PR: pendiente ·
Líneas de código y tests: 219 (límite: 400).

## Qué se hizo
- Hay un aviso de alarma con la forma y el color de su prioridad: P1 (cuadrado), P2 (triángulo),
  advertencia (rombo) o neutro (cuadrado vacío). Lleva borde izquierdo de 4 px en ese color, un título
  en negrita, el texto en tinta y, si se quiere, un botón de acción a la derecha. Sin rol por
  defecto, para que una lista de alarmas no se anuncie de golpe al lector de pantalla.
- La página de muestra tiene una sección nueva, «Botones y avisos», que exhibe botones principal,
  secundario y procesando; dos avisos informativos (uno de información y otro de confirmación) y los
  cuatro avisos de alarma, en claro y oscuro. Su contenido de ejemplo es inventado y está en
  español, marcado como tal para el lector de pantalla.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-013 | Aviso de alarma | `c6d5db7` |
| T-014 | Catálogo: botones y avisos | `d4e2ea3` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 38 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Botones y avisos» y pulsa el botón de tema para ver los
botones, los avisos y las cuatro alarmas en claro y oscuro. «Cancelar» y «Ver alarma» deben tener
borde azul grisáceo de 1 px.

## Marco teórico
- **Color solo en la forma y el borde:** el texto de una alarma va siempre en tinta; el color de la
  prioridad (que en rojo de P1 no llega al contraste necesario para texto) queda en el borde y la
  forma. Así el texto es legible y el estado se distingue también por la forma.
- **Rol de aviso (`status`, `alert`):** un `status` se anuncia sin interrumpir; un `alert`, de
  inmediato. Una lista de alarmas estática no debería anunciar todo al cargar, por eso no tienen rol
  salvo que quien las use se lo ponga.
