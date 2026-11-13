# Entrega E-02 · Verificación: botones en una fila y hueco reservado

Rama: `feat/presentacion-registro-verificacion` (sale de `feat/presentacion-registro`) · PR: [#114](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/114) ·
Líneas de código y tests: 277 (límite: 400).

## Qué se hizo
- En la pantalla de verificación del código, «Enviar otro código» y «Verificar» van ahora en la misma fila,
  alineados a la derecha y separados 10 px: el secundario a la izquierda y el principal a la derecha. Por debajo
  de 480 px de ancho no caben en una línea: pasan a una columna, cada botón a todo el ancho de la card, con
  «Verificar» arriba.
- El botón de reenviar pasa a estar dentro del formulario del código, pero no lo envía (es un botón de
  acción, no de envío) y conserva su cuenta atrás, su bloqueo y su lógica.
- Debajo del recuento de códigos («Codes you can still request: N», o del aviso de que no quedan y su enlace) hay
  un hueco reservado del alto de dos líneas de texto. Ahí aparecen el mensaje informativo del reenvío
  («Information: …»), el de espera («reintenta en N s») y los de error. Al aparecer o desaparecer uno de ellos, la
  card ya no cambia de alto. El aviso de código bloqueado, el error del formulario y el aviso de que no quedan
  códigos siguen donde estaban.
- Verificado en un navegador real con la API simulada, en claro y oscuro: a 1000 px los botones están en la misma
  fila, el secundario a la izquierda, 10 px entre ellos; a 420 px quedan en columna, con «Verificar» arriba; y la
  card mide lo mismo (376 px a 1000 px y 442 px a 420 px) antes y después de que aparezca el mensaje.
- Las reglas de CSS de la fila y del hueco se fijan con una prueba en Chromium en la entrega siguiente (E-02b).

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-003 | Botones de la verificación en una fila | `bdab27d` |
| T-004 | Hueco reservado del mensaje de reenvío | `f027cee` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 62 archivos de test en verde (809 tests).

Levanta la aplicación, con el backend levantado:
```bash
pnpm --filter frontend dev
```
Abre el enlace de verificación que llega por correo (http://localhost:5173/register/continue#<PUBLIC_ID>, donde
<PUBLIC_ID> es el identificador de tu registro). Verás los dos botones en una fila. Cuando la cuenta atrás
termine, pulsa «Enviar otro código»: el mensaje «Information: …» aparece debajo del recuento sin mover la card.
Estrecha la ventana por debajo de 480 px: los botones pasan a una columna con «Verificar» arriba.

## Marco teórico
- **Reservar espacio:** el mensaje ocupa un hueco que ya estaba apartado, de modo que aparecer o desaparecer no
  mueve lo que hay debajo; es la misma idea que la reserva del error de los campos.
- **Columna invertida (`column-reverse`):** en el HTML el botón secundario va antes que el principal (como en la
  guía); en pantallas estrechas el navegador los coloca en columna con el último arriba. Efecto conocido: con el
  teclado, Tab pasa primero por el botón que queda debajo.
