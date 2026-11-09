# Pantallas de referencia

Páginas HTML aprobadas que fijan el aspecto de la interfaz. Los componentes llevan el atributo
`data-ui` (por ejemplo `sidebar`, `topbar`, `tab`, `block`, `button-primary`), que es el contrato
común entre estas páginas y los futuros componentes React.

- `crear-empresa.html`: pantalla base (menú, barra superior, formulario). Aprobada.
- `activos.html`: pantalla de datos (tabla, indicadores, avisos de alarma, chips). Aprobada.

## Test de comparación

Mide los estilos calculados de cada componente `data-ui` en tema claro y oscuro y compara una
página candidata contra la referencia. Los componentes que no existen en la candidata se omiten;
los que existen deben coincidir. Requiere Playwright (no es dependencia del repositorio).

```bash
node docs/referencia/comparar.cjs docs/referencia/crear-empresa.html docs/referencia/activos.html
```

Deberías ver `OK: sin diferencias` y código de salida 0. Con diferencias, lista cada propiedad y
termina con código 1.
