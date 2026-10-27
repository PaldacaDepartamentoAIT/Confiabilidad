# Entrega E-05 · Campo del código de 6 dígitos

Rama: `feat/componentes-base-accesibles-codigo`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR: pendiente · Líneas de código y tests: 194 (límite: 400).

## Qué se hizo
- Un campo único para el código de verificación, no seis casillas, con su etiqueta, su asterisco
  y sus errores igual que los demás campos:
  - solo admite dígitos, hasta 6. Las letras, espacios, guiones y cualquier otro carácter se
    descartan al escribir;
  - los dígitos de ancho completo (`０`-`９`, que producen algunos teclados asiáticos) y los
    arábigos (`٠`-`٩`) se convierten a `0`-`9`;
  - en móvil abre el teclado numérico, y el sistema puede ofrecer el código recibido por SMS o
    correo con su autocompletado de códigos de un solo uso;
  - pegar sustituye todo el contenido por los 6 primeros dígitos de lo pegado, aunque el cursor esté
    en medio. Así se puede pegar un correo entero («Tu código: 98-76 54…»). Si lo pegado no tiene
    ningún dígito, el campo no cambia;
  - al completar los 6 dígitos no se envía nada ni se mueve el foco: el envío lo decide el usuario.
- La página de muestra añade el campo «Código de verificación» (obligatorio) después de la
  contraseña. La auditoría de accesibilidad sigue sin infracciones.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-015 | Normalización del código | `ef52612` |
| T-016 | Campo del código | `7278320` |
| T-017 | Código en la página de muestra | `f2cf350` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 82 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el campo «Código de verificación *» al final
del formulario.

Pruébalo:
1. Pulsa Tab hasta el campo del código y escribe `1a2b3c4d5e6f7`. Deberías ver `123456`: las
   letras se descartan y el séptimo dígito no entra.
2. Borra el campo, escribe `12`, coloca el cursor entre el 1 y el 2, y pega este texto:
   «Tu código: 98-76 54 321». Deberías ver `987654`.
3. Pega un texto sin números, como «hola». Deberías ver que el código no cambia.
4. Comprueba que, con los 6 dígitos escritos, el foco sigue en el campo y la página no hace nada
   más.

En un móvil (o en DevTools con la vista de dispositivo móvil), al tocar el campo deberías ver el
teclado numérico.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Fuera de esta entrega
Los errores de cada campo al salir de él llegan en E-06, y el envío del formulario, en E-07.
