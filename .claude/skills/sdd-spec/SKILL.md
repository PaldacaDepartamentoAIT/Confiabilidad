---
name: sdd-spec
description: 'Especifica una feature nueva en SDD entrevistando al usuario pregunta a pregunta y genera specs/FEATURE/spec.md con requisitos funcionales en EARS, supuestos, fuera de alcance y criterios de finalización. Usar siempre que el usuario quiera definir, especificar o empezar una feature o funcionalidad nueva, escribir requisitos o "hacer la spec", aunque no diga la palabra spec. No usar para modificar una spec existente (sdd-cambio) ni para diseño técnico (sdd-plan).'
---

# SDD · Spec

Entrevista al usuario y redacta qué debe hacer la feature y por qué. No hables de tecnología, módulos ni diseño: esas decisiones corresponden al plan, y si aparecen aquí condicionan los requisitos antes de tiempo.

## Datos necesarios

- **Feature**: nombre en kebab-case para la carpeta (por ejemplo, `login-con-google`).
- **Idea inicial**: una descripción breve de lo que se quiere construir.
- **Máximo de preguntas**: lee `sdd.max_preguntas_spec` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo. Si falta la configuración, sugiere además añadirla a `CLAUDE.md`.

## Precondiciones

- [ ] Existe `specs/constitution.md` con `Estado: aprobada`.
- [ ] No existe `specs/<feature>/spec.md`. Si existe, esta feature ya está especificada y cualquier cambio debe hacerse con `sdd-cambio`.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar la spec. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento

1. Lee `specs/constitution.md`.
2. Haz preguntas de una en una, sin superar el máximo configurado. Cubre alcance, casos límite, errores y lo que queda fuera de alcance. Prioriza las preguntas cuya respuesta cambiaría más requisitos.
3. Si el usuario responde "no sé", propón una opción razonable y regístrala como supuesto (`S-01`…). No la conviertas en requisito sin marcarla.
4. Genera `specs/<feature>/spec.md` con la plantilla de `references/plantilla.md`, con `Estado: borrador`.
   - Escribe cada RF con uno de los patrones EARS de la plantilla y con ID correlativo (`RF-001`…).
   - Cada RF describe un comportamiento observable y verificable.
5. Muestra la spec al usuario.
6. No marques la spec como aprobada: la aprobación se hace tras la clarificación. Indica el siguiente paso: `sdd-clarificar`.

## Detente si

- Un requisito contradice un principio de la constitución: señálalo y pregunta al usuario cómo resolverlo antes de escribirlo.
