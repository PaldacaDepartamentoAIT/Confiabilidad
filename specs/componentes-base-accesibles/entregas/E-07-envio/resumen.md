# Entrega E-07 · Envío con foco al primer error y mensaje de demostración

Rama: `feat/componentes-base-accesibles-envio`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#27](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/27) ·
Líneas de código y tests: 403 (límite con la excepción aprobada en `tasks.md`: 500).

## Qué se hizo
- Un botón accesible:
  - su nombre para el lector es su texto visible;
  - se activa con clic, Enter y Espacio;
  - por defecto no envía formularios: solo lo hace si se indica de forma explícita.
- Enviar el formulario, con el botón «Verificar» o con Enter desde cualquier campo:
  - valida todos los campos a la vez;
  - si hay errores, los muestra y lleva el foco al primer campo con error, en orden visual. El
    error se pinta antes de mover el foco, para que el lector de pantalla lea el campo junto con su
    error;
  - si todo es válido, muestra un mensaje de demostración («Información: Formulario de
    demostración: no se envían datos.») y le lleva el foco, para que el lector lo lea;
  - el mensaje se retira en el siguiente envío.
- Un componente de mensaje general (error, éxito o información) con un prefijo visible y
  traducido que dice qué tipo de mensaje es. Puede recibir el foco desde el código, pero no está en
  el orden de Tab. Se traduce al cambiar de idioma.
- Una corrección encontrada al probar en Chromium (T-034). Si al pulsar «Verificar» con el ratón
  desaparecía el error del campo que se dejaba, el botón se movía hacia arriba antes de soltar el
  ratón y el clic se perdía. Ahora pulsar «Verificar» con el ratón no saca el foco del campo, así
  que nada se mueve y el envío llega. Con teclado no cambia nada.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-021 | Botón | `dabc24e` |
| T-022 | Validación al enviar y foco al primer error | `c887a6b` |
| T-023 | Mensaje general | `8b7de5d` |
| T-024 | Envío en la página de muestra | `5bcdd10` |
| T-034 | Corrección: el clic de envío se pierde cuando un error desaparece al salir del campo | `9e12494` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 135 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el botón «Verificar» al final del formulario.

Pruébalo:
1. Con el formulario vacío, haz clic en «Nombre completo» y pulsa Enter. Deberías ver un error bajo
   cada campo y el foco en «Nombre completo».
2. Rellena el nombre, la contraseña y el código con `12345`, deja el correo vacío y pulsa Enter
   desde el código. Deberías ver el foco en «Correo electrónico», con su error, y el error del
   código.
3. Escribe el correo (`ana@planta.com`), completa el código con un sexto dígito y pulsa
   «Verificar» con el ratón. Deberías ver arriba del formulario «Información: Formulario de
   demostración: no se envían datos.» con el foco, aunque al salir del código haya desaparecido
   su error.
4. Borra el nombre y vuelve a pulsar «Verificar». Deberías ver que el mensaje de demostración
   desaparece y el foco vuelve a «Nombre completo».

Con un lector de pantalla, en los pasos 1 a 3 deberías oír el nombre del campo seguido de su error,
y en el paso 3, el mensaje con su prefijo «Información:».

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Fuera de esta entrega
El estado «Procesando…» del botón durante 3 segundos y su aviso al lector llegan en E-08. Los
mensajes generales de error y el botón de error de ejemplo, en E-09.
