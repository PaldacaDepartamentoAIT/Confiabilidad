---
name: sdd-plan
description: 'Genera o actualiza el plan técnico de una feature SDD (specs/FEATURE/plan.md) a partir de la constitución y la spec aprobada, con módulos, modelo de datos, decisiones justificadas frente a su alternativa, estrategia de tests y trazabilidad de cada requisito. Usar cuando el usuario quiera diseñar, planificar o definir la arquitectura de una feature ya especificada, o actualizar el plan tras un cambio. No escribe código; no usar para dividir en tareas (sdd-tareas).'
---

# SDD · Plan

Diseña cómo se va a construir la feature, sin escribir código. Cada decisión se justifica frente a una alternativa descartada, y la matriz de trazabilidad garantiza que ningún requisito se quede sin diseñar.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.

Si falta, pídelo al usuario y no continúes hasta tenerlo.

## Precondiciones

- [ ] Existe `specs/constitution.md` con `Estado: aprobada`.
- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] Ninguna entrada del historial de la spec está en `pendiente de clarificar`.
- [ ] Si ya existe `plan.md`: la última entrada del historial de la spec está en `impacto analizado` y ese análisis indica que el plan debe cambiar. Si no es así, pregunta al usuario si quiere actualizar el plan igualmente.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar el plan. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento

1. Lee la constitución, la spec y, si existe, el plan actual. Explora el código existente relacionado para que el diseño encaje con él.
2. Redacta el plan con la plantilla de `references/plantilla.md`, con `Estado: borrador`. No escribas código.
   - Cada decisión (`D-XX`) incluye la alternativa descartada y el motivo.
   - Completa la matriz de trazabilidad con todos los RF no obsoletos.
   - Lista explícitamente los RF sin cobertura.
   - Si actualizas un plan existente, conserva los IDs `M-XX` y `D-XX` y añade los nuevos con el siguiente ID libre.
3. Muestra el plan y espera la aprobación del usuario.
4. No lo marques como aprobado mientras haya RF sin cobertura: `sdd-tareas` no podrá continuar y el problema solo se desplazaría.
5. Cuando el usuario apruebe, cambia a `Estado: aprobado`.
6. Indica el siguiente paso: `sdd-tareas`.

## Detente si

- Una decisión necesaria choca con un principio de la constitución: explícalo y no continúes hasta que el usuario decida.
- Descubres que la spec es ambigua o incompleta para diseñar: indícalo y remite a `sdd-cambio`.
