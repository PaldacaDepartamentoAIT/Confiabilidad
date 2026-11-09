# Entrega E-03 · Iconos, formas de alarma y chip

Rama: `feat/sistema-de-diseno-iconos` · PR: pendiente ·
Líneas de código y tests: 315 (límite: 400).

## Qué se hizo
- Se instala `lucide-react` (versión 1.70.0) y hay un módulo de iconos con los 22 de las pantallas
  de referencia (casa, edificio, fábrica, paquete, llave, campana, archivo, ajustes, globo, sol,
  luna, lupa, menú, paneles, chevrons, verificación, información y alerta). Cada uno mide 16 px, con
  trazo de 2 px y oculto al lector de pantalla; el tamaño se puede cambiar (el botón del menú usará
  22 px).
- Hay un componente para las cuatro formas de alarma: P1 es un cuadrado, P2 un triángulo,
  advertencia un rombo y neutro un cuadrado vacío, cada una con el color de su prioridad. Si se le da
  una etiqueta, el lector de pantalla la anuncia; si no, se oculta.
- Hay un chip de 12 px para etiquetas como la criticidad.
- Esta entrega no muestra nada nuevo en pantalla: bloques, chips y formas se ven en el catálogo en
  E-03b. La entrega original medía 665 líneas y, por el límite de 400, se dividió por decisión del
  usuario.
- Dependencia nueva: `lucide-react` (aprobada por el usuario al definir la feature).

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-006 | `lucide-react` y módulo de iconos | `b853317` |
| T-007 | Formas de alarma | `aee286d` |
| T-009 | Chip | `bc06755` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 35 archivos de test en verde, entre ellos `src/icons/icons.test.tsx` (25 tests),
`src/icons/shapes.test.tsx` (9) y `src/components/Chip.test.tsx` (3).

## Marco teórico
- **Forma y color a la vez:** un estado de alarma nunca se comunica solo con color: cada prioridad
  tiene también una forma distinta (cuadrado, triángulo, rombo, cuadrado vacío). Así se distingue
  con daltonismo y en blanco y negro.
- **Icono oculto al lector de pantalla:** un icono que acompaña a un texto es decoración, y leerlo
  sería ruido. Por eso lleva `aria-hidden`; solo se anuncia cuando él mismo es el único contenido y
  se le da una etiqueta.
