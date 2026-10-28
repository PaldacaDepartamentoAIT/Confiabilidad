# Entrega E-08 · Botón «Procesando…» durante 3 segundos con aviso al lector

Rama: `feat/componentes-base-accesibles-procesando`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#29](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/29) ·
Líneas de código y tests: 374 (límite: 400).

## Qué se hizo
- Un **anunciador** para el lector de pantalla: dos regiones invisibles, una «educada» (espera a
  que el lector termine lo que está diciendo) y otra «urgente» (lo interrumpe). Existen desde que
  carga la página, porque los lectores solo anuncian los cambios de una región que ya estaba, y se
  vacían antes de cada aviso, para que un mismo texto repetido se anuncie otra vez.
- El **botón** tiene un estado «procesando»:
  - su texto, y con él el nombre que lee el lector, pasa a «Procesando…»;
  - ignora clics, Enter y Espacio, y un botón de envío deja de enviar, también con Enter desde un
    campo;
  - no se desactiva del todo: sigue en el orden de Tab y no pierde el foco, para que quien usa
    teclado no se quede sin saber dónde está;
  - al entrar en ese estado, el lector oye «Procesando» por la región educada. Al salir no se
    anuncia nada: lo que llega después ya habla por sí mismo.
- La **página de muestra**, con un envío válido, pone «Verificar» en «Procesando…» durante 3
  segundos y después muestra el mensaje de demostración con el foco. Pulsar otra vez durante la
  espera no hace nada.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-025 | Anunciador | `81b0b06` |
| T-026 | Botón procesando | `2f3ec9c` |
| T-027 | Simulación de envío de 3 segundos | `f8b9462` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 164 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el formulario de ejemplo.

Pruébalo con el teclado:
1. Rellena todos los campos con valores válidos. Por ejemplo, la nueva contraseña
   `turbina-compresor-7` y el código `123456`.
2. Pulsa Tab hasta «Verificar» y pulsa Enter. Deberías ver que el botón dice «Procesando…» y que el
   foco sigue en él.
3. Pulsa Enter otra vez antes de 3 segundos. Deberías ver que no pasa nada distinto.
4. A los 3 segundos, deberías ver que el botón vuelve a decir «Verificar» y que aparece
   «Información: Formulario de demostración: no se envían datos.» con el foco.

Con un lector de pantalla, en el paso 2 deberías oír «Procesando» y, en el paso 4, el mensaje de
demostración. Sin lector, en DevTools (F12) → **Elements** puedes ver el texto «Procesando» dentro
del elemento con `role="status"` al final de la página.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Comprobado por el usuario en local el 2026-10-28.

## Marco teórico
**Regiones vivas (`aria-live`).** Son zonas de la página cuyo cambio de texto el lector de pantalla
anuncia aunque el foco esté en otro sitio. Una región «educada» espera a que el lector termine de
hablar y una «urgente» lo interrumpe; por eso «Procesando» va por la educada. Dos detalles hacen
que funcionen de verdad: la región tiene que existir antes del cambio (una región que aparece ya con
texto suele no anunciarse) y, para repetir el mismo aviso, hay que vaciarla antes de volver a
escribirlo.

## Fuera de esta entrega
Los mensajes generales de error junto a errores de campo, el botón de error de ejemplo y el cierre
de la feature llegan en E-09.
