# Entrega E-10 · Contraseña nueva con sus reglas y su ayuda visible

Rama: `feat/componentes-base-accesibles-contrasena-nueva`, con PR contra la rama de integración
`feat/componentes-base-accesibles` · PR: pendiente · Líneas de código y tests: 175 (límite: 400).

Se hizo después de E-07 y antes de E-08, porque no depende de ellas. Nació de un `sdd-cambio` que
añadió RF-026 y RF-027 y cambió RF-020 y RF-021.

## Qué se hizo
- Los campos de texto aceptan un **texto de ayuda** visible bajo el campo. El lector de pantalla lo
  lee al llegar al campo y, si hay un error, lee la ayuda y después el error.
- El campo de **contraseña nueva** (no el de la actual) muestra siempre su ayuda: «Al menos 12
  caracteres, no solo números.».
- Unas **reglas de contraseña nueva** reutilizables, copiadas de las del servidor:
  - al menos 12 caracteres, contados como los cuenta el servidor. Por eso, 6 emojis son 6
    caracteres, aunque el navegador los mida como 12;
  - no puede ser solo dígitos, de cualquier sistema de escritura (`123…`, `１２３…`, `١٢٣…`).
- El resto de la política del servidor (parecido al correo o al nombre, contraseñas comunes y
  filtradas) no se comprueba en el navegador. El servidor la decide al enviar (decisión D-18).
- La **contraseña actual** no aplica estas reglas: bloquearían a cuentas con contraseñas anteriores
  a la política y revelarían la política en el inicio de sesión.
- La página de muestra añade el campo «Nueva contraseña» (obligatorio) tras la contraseña actual.

**Riesgo conocido (S-11):** las reglas están duplicadas a mano, porque backend y frontend no
comparten código. Si el servidor cambia el mínimo de 12, hay que cambiarlo también en
`frontend/src/forms/passwordRules.ts`.

## Tareas
El detalle de cada tarea, con su «Hecho cuando» y sus decisiones, está en
[`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-035 | Textos de la contraseña nueva | `62bb82f` |
| T-036 | Texto de ayuda ligado al campo | `95c5c6e` |
| T-037 | Reglas de la contraseña nueva | `d0d5053` |
| T-038 | Contraseña nueva con su ayuda | `52c67b4` |
| T-039 | Contraseña nueva en la página de muestra | `633ed25` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 152 tests en verde.

Arranca la página:
```bash
pnpm --filter frontend dev
```
Deberías ver la página en http://localhost:5173 con el campo «Nueva contraseña *» y, debajo, «Al
menos 12 caracteres, no solo números.».

Pruébalo:
1. Escribe `abc` en «Nueva contraseña» y haz clic en «Código de verificación». Deberías ver «Usa al
   menos 12 caracteres.» bajo la ayuda.
2. Cambia la nueva contraseña a `123456789012` y vuelve a salir. Deberías ver «No uses solo
   números.».
3. Cámbiala a `turbina-compresor-7` y sal. Deberías ver que el error desaparece y queda solo la
   ayuda.
4. Escribe `abc` en «Contraseña» (la actual) y sal. Deberías ver que no aparece ningún error: la
   contraseña actual no tiene esas reglas.

En DevTools (F12) → **Elements** → **Accessibility**, con «Nueva contraseña» seleccionada, deberías
ver la ayuda como **Description** y, si hay error, la ayuda seguida del error.

Con Docker, desde la raíz del repositorio:
```bash
docker compose -f docker/docker-compose.yml up frontend
```
Deberías ver la misma página en http://localhost:5173. Esta vía no se pudo comprobar en el entorno
remoto (el contenedor no tiene salida a internet); está pendiente en
[`HUMAN_TODO.md`](../../HUMAN_TODO.md).

## Fuera de esta entrega
Las dos contraseñas tienen un botón llamado igual, «Mostrar contraseña». Está pendiente de decidir
si cada botón debe nombrar su campo.
