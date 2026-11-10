# Entrega E-09b · Contraer el menú lateral y su pie

Rama: `feat/sistema-de-diseno-menu-lateral-pie` · PR: [PaldacaDepartamentoAIT/Confiabilidad#84](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/84) ·
Líneas de código y tests: 285 (límite: 400).

## Qué se hizo
- El menú lateral se puede contraer y expandir con un botón a la derecha de su cabecera: un chevron
  de 22 px, «<» con el menú abierto y «>» con él contraído. Contraído mide 60 px y solo se ven los
  iconos, que no se mueven; la etiqueta de cada elemento pasa a ser su `title`. El cambio de ancho
  se anima en 0,25 s y las etiquetas se desvanecen en 0,18 s. El botón anuncia su estado
  (`aria-expanded`) y se llama «Contraer menú» o «Expandir menú» (en los tres idiomas).
- Tiene un pie, separado por una línea, con el botón de tema, debajo el de idioma y debajo el del
  usuario (avatar con iniciales, nombre y flechas arriba y abajo). El usuario es un botón solo si la
  pantalla le pasa una acción; si no, se ve igual pero no se puede pulsar.
- En la página de muestra, la sección «Menú lateral» exhibe el menú con usuario y se puede contraer y
  expandir. Con él la página tiene dos botones de tema: el de la barra superior y el del pie del menú.
- Verificado en un navegador real, en claro y oscuro: 232 px abierto y 60 px contraído; un fallo
  que solo se veía en pantalla (los iconos se encogían a un punto al contraer) quedó corregido.
- Esta parte salió de la entrega del menú lateral (594 líneas), dividida por la regla de `AGENTS.md`.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-060 | Contraer y expandir el menú lateral | `0ab85e9` |
| T-061 | Pie del menú lateral: tema, idioma y usuario | `0ab85e9` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 44 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Menú lateral», pulsa el botón de la cabecera para contraerlo
y expandirlo (también con Tab e Intro) y comprueba el pie: tema, idioma y usuario.

## Marco teórico
- **Botón que alterna un estado:** el botón de contraer cambia su nombre y su `aria-expanded` según
  el estado, para que el lector de pantalla diga si el menú está abierto o cerrado.
- **Etiqueta como `title`:** con el menú contraído solo se ven los iconos; el `title` de cada
  elemento muestra su nombre al pasar el cursor, y el lector de pantalla sigue leyendo la etiqueta.
