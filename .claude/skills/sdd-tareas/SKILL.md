---
name: sdd-tareas
description: 'Divide el plan aprobado de una feature SDD en tareas pequeñas, ordenadas por dependencia y verificables, en specs/FEATURE/tasks.md, o actualiza las tareas tras un cambio. Usar cuando el usuario quiera desglosar, trocear o planificar el trabajo de implementación, crear el backlog o la lista de tareas de una feature. No usar para implementar (sdd-implementar) ni para diseñar (sdd-plan).'
---

# SDD · Tareas

Trocea el plan en tareas pequeñas: producen diffs que se pueden revisar de verdad y errores que se detectan pronto. El límite de archivos por tarea es una alarma: si una tarea toca muchos, casi seguro son varias tareas juntas.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.
- **Máximo de archivos por tarea**: lee `sdd.max_archivos_tarea` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo. Si falta la configuración, sugiere además añadirla a `CLAUDE.md`.

## Precondiciones

- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] Existe `specs/<feature>/plan.md` con `Estado: aprobado`.
- [ ] La sección "RF sin cobertura" del plan está vacía o dice "ninguno".
- [ ] Si ya existe `tasks.md`: la última entrada del historial de la spec está en `impacto analizado` y el plan (si debía cambiar) ya está aprobado de nuevo.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar las tareas. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento

1. Lee la spec y el plan. Si existe `tasks.md`, léelo también.
2. Divide el plan en tareas con la plantilla de `references/plantilla.md`, con `Estado: borrador`:
   - Cada tarea implementa un único comportamiento observable e incluye sus tests.
   - Cada tarea toca como máximo el número configurado de archivos; si no cabe, divídela. Si no se puede dividir (andamiaje, renombrados, configuración repartida), añade una línea `Excepción:` que explique por qué.
   - Ordénalas por dependencia.
   - La línea `Hecho cuando:` debe poder comprobarse ejecutando algo concreto.
3. Si actualizas un `tasks.md` existente: conserva los IDs y el estado de las tareas hechas, añade las nuevas con el siguiente ID libre y, si una tarea hecha queda afectada por el cambio, no la desmarques: crea una tarea nueva que la ajuste y explícalo.
4. Comprueba que todo RF no obsoleto aparece en al menos una tarea y lista los que no.
5. Muestra las tareas y espera la aprobación del usuario. Cuando apruebe, cambia a `Estado: aprobado`.
6. Indica el siguiente paso: `sdd-implementar` con la primera tarea.

## Detente si

- Para cubrir un RF hace falta algo que el plan no contempla: indícalo y remite a `sdd-plan`.
