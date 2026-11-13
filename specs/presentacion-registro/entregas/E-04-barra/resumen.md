# E-04 Barra superior compartida

## Qué se hizo
`App` pinta una sola barra superior (nombre del sistema, idioma y tema) para las tres pantallas del registro y
cambia solo el contenido: al pasar del registro a la verificación o a la cuenta creada, la barra es el mismo
nodo y no se repinta ni se anima. Las páginas dejan de pintarla (y de recibir `storage`). El catálogo conserva
su propia barra. Al mover la barra apareció un fallo: el secundario bloqueado cambiaba de fondo al pasar el
puntero, porque el orden de carga del CSS dejó de favorecer a `Button.css`; se corrige con una regla más
específica (T-014).

## Tareas
- T-012 (barra superior compartida) — commit `d1a28a4`.
- T-014 (hover del botón secundario bloqueado que no dependa del orden del CSS) — commit de esta entrega.

## Cómo ejecutarlo y probarlo
```bash
pnpm --filter frontend test
```

Deberías ver 838 pruebas en verde.

```bash
pnpm --filter frontend test:visual
```

Deberías ver 56 pruebas visuales en verde, entre ellas la del botón bloqueado sin hover.

Para verlo en el navegador, arranca el frontend:

```bash
pnpm --filter frontend dev
```

Abre `/register` y, en la consola del navegador, ejecuta `history.pushState(null, "", "/register/done"); dispatchEvent(new PopStateEvent("popstate"))`:
la barra superior no parpadea ni se mueve mientras cambia la card.

## Líneas
Ver el PR.

## PR
Pendiente.
