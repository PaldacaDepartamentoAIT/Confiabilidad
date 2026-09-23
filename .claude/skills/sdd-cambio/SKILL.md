---
name: sdd-cambio
description: 'Introduce un requisito nuevo, modificado o eliminado en una feature SDD ya especificada, actualizando primero la spec sin tocar código, y después analiza el impacto sobre el plan, las tareas y los tests. Usar siempre que el usuario pida cambiar, añadir, quitar o ajustar el comportamiento de una feature existente, aunque lo formule como una petición de código ("haz que además…", "cambia para que…"). No usar para features nuevas (sdd-spec) ni para bugs donde la spec ya describe el comportamiento correcto (sdd-implementar).'
---

# SDD · Cambio

La spec es la fuente de verdad: si el código cambia sin que cambie la spec, dejan de coincidir y el resto del flujo pierde sentido. Por eso primero se cambia la spec, después se clarifica, después se mide el impacto y solo entonces se toca código.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.
- **Nuevo requisito** (solo en modo spec): qué debe cambiar y por qué.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo.

## Modo

Determínalo por el estado de la spec e indícaselo al usuario:

- **Modo spec**: no hay ninguna entrada del historial en `pendiente de clarificar` ni en `clarificado`. Se registra el cambio en la spec.
- **Modo impacto**: la última entrada del historial está en `clarificado`. Se analiza el impacto.

## Precondiciones

Modo spec:
- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] Ninguna entrada del historial está en `pendiente de clarificar`. Si la hay, el cambio anterior no se ha cerrado: el siguiente paso es `sdd-clarificar`.

Modo impacto:
- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] La última entrada del historial está en `clarificado`.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar el cambio. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento: modo spec

1. Lee la spec. No toques código, plan ni tareas.
2. Prepara los cambios en la spec:
   - Los RF modificados conservan su ID.
   - Los nuevos toman el siguiente ID libre.
   - Los eliminados se marcan como `OBSOLETO` con el motivo; no se borran, porque los tests y las tareas que los citan deben seguir siendo rastreables.
   - Añade una entrada al historial con los RF afectados y `Estado: pendiente de clarificar`.
   - Cambia la spec a `Estado: borrador`.
3. Muestra el diff y espera la aprobación del usuario antes de escribir.
4. Cuando apruebe, escribe los cambios e indica el siguiente paso: `sdd-clarificar`.

## Procedimiento: modo impacto

1. Lee la spec, el plan, las tareas y los tests relacionados con los RF de la última entrada del historial.
2. Para cada RF cambiado, indica qué secciones de `plan.md`, qué tareas de `tasks.md` y qué tests quedan afectados, con el formato de `references/plantilla.md`.
3. No modifiques nada: el plan lo actualiza `sdd-plan` y las tareas `sdd-tareas`. Muestra el análisis y espera la aprobación del usuario.
4. Cuando apruebe, marca la entrada del historial como `impacto analizado` e indica el siguiente paso: `sdd-plan` si el plan se ve afectado, o `sdd-tareas` si no.
