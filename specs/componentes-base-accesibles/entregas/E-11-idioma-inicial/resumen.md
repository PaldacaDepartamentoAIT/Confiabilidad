# Entrega E-11 · Idioma del documento antes de crear la página

Rama: `fix/componentes-base-accesibles-idioma-inicial`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR: pendiente · Líneas de código y tests: 23 (límite: 400).

## Qué se hizo
El checklist con NVDA + Chrome (CF-5) encontró que, con la página en inglés, los campos y los
controles se leían con voz española. `index.html` declara `lang="es"` y el idioma activo se
aplicaba después de que React creara los elementos; Chrome fija el idioma de cada elemento al
crearlo. Ahora `main.tsx` fija `<html lang>` con el idioma inicial antes de montar la página.

Esto corrige el idioma al abrir o recargar la página. El cambio en vivo con el selector sigue
pendiente de decisión (RF-006): los elementos que ya existían conservan su idioma.

## Tareas
El detalle está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-041 | Corrección: idioma del documento fijado antes de crear la página | `a9e97a4` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, cambia a la rama de la entrega:
```bash
git fetch origin fix/componentes-base-accesibles-idioma-inicial
```
```bash
git checkout fix/componentes-base-accesibles-idioma-inicial
```

Instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 186 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```

Con NVDA + Chrome:
1. Abre http://localhost:5173 y pulsa «English».
2. Recarga la página con F5.
3. Recorre la página con Tab. Deberías oír con voz inglesa todos los campos y los dos «Show
   password (…)», no solo los botones.

Sin lector, en DevTools (F12) → **Elements**, deberías ver `<html lang="en">` desde la carga.
