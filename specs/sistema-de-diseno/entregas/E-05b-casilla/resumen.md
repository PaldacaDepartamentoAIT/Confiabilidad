# Entrega E-05b · Casilla de verificación y sección «Campos» del catálogo

Rama: `feat/sistema-de-diseno-casilla` · PR: [PaldacaDepartamentoAIT/Confiabilidad#74](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/74) ·
Líneas de código y tests: 262 (límite: 400).

## Qué se hizo
- La casilla de verificación tiene la identidad nueva: caja de 18 px con borde de 1 px y esquinas de
  4 px; al marcarla se rellena con el color principal y muestra un icono de verificación de 14 px
  centrado; al pasar el cursor sin marcar se tiñe con el 9 % de la tinta, y marcada se oscurece. La
  etiqueta queda a su lado, y la ayuda y el error (con icono) debajo de la fila, alineados con el borde de la caja, sin sangría.
- La casilla de las pantallas de registro (términos y avisos) se ve así sin cambiar su comportamiento.
- La página de muestra tiene una sección nueva, «Campos», que exhibe campos de texto (con ayuda, con
  error y obligatorio), de contraseña y de código, y tres casillas (marcada, sin marcar y con error),
  en claro y oscuro. Su contenido de ejemplo es inventado y está en español, marcado como tal.
- Dejo una cosa abierta: el borde de la casilla con error no se pone rojizo, porque la guía solo
  define el borde de error para los campos de texto.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-017 | Casilla de verificación | `30cbe80` |
| T-018 | Catálogo: campos | `1b11945` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 39 archivos de test en verde.

Levanta la aplicación:
```bash
pnpm --filter frontend dev
```
Abre http://localhost:5173/, baja hasta «Campos», marca y desmarca las casillas (clic en la caja o en
el texto, y con la barra espaciadora) y pulsa el botón de tema para verlas en claro y oscuro.

## Marco teórico
- **Casilla nativa con apariencia propia:** la caja es un `input type="checkbox"` real, al que se le
  quita el aspecto del navegador. Así conserva el teclado, el estado y el lector de pantalla sin
  código adicional; el icono de verificación se dibuja encima y solo se ve cuando está marcada.
- **Ayuda fuera de la etiqueta:** si el texto de ayuda estuviera dentro de la etiqueta, el lector de
  pantalla lo leería como parte del nombre de la casilla. Por eso va debajo, enlazada como descripción.
