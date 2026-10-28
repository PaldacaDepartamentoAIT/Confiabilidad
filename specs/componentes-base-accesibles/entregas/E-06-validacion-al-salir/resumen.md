# Entrega E-06 · Errores de campo al salir de cada campo

Rama: `feat/componentes-base-accesibles-validacion-al-salir`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR:
[PaldacaDepartamentoAIT/Confiabilidad#26](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/26) ·
Líneas de código y tests: 363 (límite: 400).

## Qué se hizo
- Una pieza común de validación de formularios que comprueba cada campo **al salir de él**, desde
  la primera vez, aunque no se haya enviado nada (decisión C-04 de la clarificación):
  - si el campo no cumple una regla, aparece su error; si se corrige y se vuelve a salir, el error
    desaparece;
  - solo se valida el campo del que se sale, nunca los demás;
  - la contraseña y su botón «Mostrar contraseña» cuentan como un solo campo: pasar del uno al
    otro no muestra el error, y salir de los dos sí valida la contraseña (cambio de RF-025 pedido
    durante la entrega, con la decisión C-14);
  - con varias reglas, se muestra la primera que falla (por ejemplo, «obligatorio» antes que
    «formato de correo»);
  - el error se guarda como una clave de traducción, no como texto. Por eso, al cambiar de idioma,
    los errores visibles se traducen sin perderse.
- Las reglas de la página de muestra:
  - todos los campos son obligatorios (vacío o solo espacios es un error);
  - el correo necesita exactamente una `@`, con algo antes y después y sin espacios. Es una
    comprobación mínima: la definitiva la hará el servidor (decisión C-07);
  - el código necesita exactamente 6 dígitos.
- La página de muestra ya muestra estos errores: debajo de cada campo, ligados a él (el lector de
  pantalla los lee al llegar al campo) y con el campo marcado como no válido.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md). T-019 se hizo antes que T-018 porque define los tipos de error que
usan las reglas de la página. T-033 se añadió durante la entrega con un `sdd-cambio` de RF-025.

| Tarea | Título | Commit |
|---|---|---|
| T-019 | Validación al salir de cada campo | `da23a2b` |
| T-018 | Reglas de validación de la página de muestra | `b0d6ad9` |
| T-020 | Errores al salir en la página de muestra | `70a3f50` |
| T-033 | Contraseña y su control como un solo campo al salir | `7b00a1f` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 115 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el formulario de ejemplo.

Pruébalo:
1. Escribe `a@` en «Correo electrónico» y pulsa Tab. Deberías ver debajo «Escribe un correo como
   nombre@empresa.com.».
2. Pulsa «Português (Brasil)». Deberías ver el mismo error en portugués: «Digite um e-mail como
   nome@empresa.com.».
3. Vuelve al correo, complétalo (`ana@planta.com`) y pulsa Tab. Deberías ver que el error
   desaparece.
4. Entra en «Nombre completo» sin escribir nada y pulsa Tab. Deberías ver «Completa este campo.».
5. Escribe `12345` en «Código de verificación» y pulsa Tab. Deberías ver «Escribe los 6 dígitos del
   código.».
6. Recarga la página, entra en «Contraseña» sin escribir y pulsa Tab: el foco pasa a «Mostrar
   contraseña» y no aparece ningún error. Pulsa Tab otra vez para ir al código. Deberías ver
   «Completa este campo.» bajo la contraseña.

En DevTools (F12) → **Elements** → **Accessibility**, con un campo con error seleccionado, deberías
ver **Invalid user entry** en `true` y el mensaje como **Description**.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Comprobado por el usuario en local el 2026-10-28.

## Fuera de esta entrega
Todavía no hay botón de envío: validar todo el formulario al enviar y llevar el foco al primer
error llega en E-07.
