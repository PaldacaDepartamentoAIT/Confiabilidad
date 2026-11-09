# Entrega E-04 · Botón con variantes y aviso informativo

Rama: `feat/sistema-de-diseno-boton-aviso` · PR: pendiente ·
Líneas de código y tests: 209 (límite: 400).

## Qué se hizo
- El botón tiene ahora la identidad nueva y dos variantes: principal (relleno en el color principal,
  que se oscurece al pasar el cursor) y secundario (solo borde de 1 px y texto en el color principal,
  que se tiñe con el 9 % de la tinta al pasar el cursor). Mide 36 px de alto, con esquinas de 6 px.
  Se comporta igual que antes: el estado «procesando», el anuncio al lector de pantalla y el foco
  conservado no cambian. Los botones de las pantallas de registro y de la página de muestra siguen
  siendo principales y ya se ven con el estilo nuevo.
- Hay un componente de aviso informativo: borde izquierdo de 4 px en el color de texto secundario,
  icono de información (o de verificación para confirmaciones) y texto en tinta. Por defecto se
  anuncia como estado; se puede cambiar su rol.
- Esta entrega no añade secciones nuevas al catálogo. El aviso de alarma y la sección «Botones y
  avisos» llegan en E-04b. La entrega original medía 428 líneas y, por el límite de 400, se dividió
  por decisión del usuario.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-011 | Botón restilizado | `b98c783` |
| T-012 | Aviso | `24eced1` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 37 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/ y comprueba que los botones «Verificar» y «Mostrar error general de
ejemplo» tienen el relleno azul grisáceo, 36 px de alto y esquinas de 6 px, y que oscurecen al pasar
el cursor.

## Marco teórico
- **Variante de un componente:** el botón es uno solo y la propiedad `variant` decide si es principal
  o secundario. Así toda la aplicación pide «un botón secundario» sin repetir sus estilos.
- **`aria-disabled` en lugar de `disabled`:** mientras el botón procesa, sigue en el orden del teclado
  y no pierde el foco; solo ignora los clics. Su aspecto (opacidad 0,6) lo marca como inactivo.
