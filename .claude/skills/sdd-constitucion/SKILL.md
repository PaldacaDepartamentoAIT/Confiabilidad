---
name: sdd-constitucion
description: 'Crea o revisa la constitución de un proyecto SDD (specs/constitution.md), es decir, los principios verificables sobre stack, calidad, tests y límites que toda feature debe respetar. Usar cuando el usuario quiera arrancar SDD en un proyecto, definir reglas, principios o estándares del proyecto, o mencione la constitución. No usar para especificar features (sdd-spec) ni para diseño técnico (sdd-plan).'
---

# SDD · Constitución

Propón las reglas del proyecto que cualquier feature debe respetar. Cada principio tiene que poder comprobarse, porque las fases posteriores (plan, implementación, validación) lo usarán como criterio y un principio que no se puede comprobar no sirve como criterio.

## Datos necesarios

- **Máximo de principios**: lee `sdd.max_principios` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta algún dato, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo. Si falta la configuración, sugiere además añadirla a `CLAUDE.md` para no preguntarla de nuevo.

## Precondiciones

Compruébalas todas antes de hacer nada:

- [ ] No existe `specs/constitution.md`.
  Si existe, no la sobrescribas: informa al usuario y pregúntale si quiere revisarla. Solo continúa en modo revisión si lo confirma; en ese modo conserva los IDs `P-XX` existentes.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar la constitución. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <qué debe hacer el usuario>
```

## Procedimiento

1. Explora el repositorio (manifiestos de dependencias, configuración de lint, formateo y tests, estructura de carpetas) para que los principios reflejen el proyecto real y no uno genérico.
2. Pregunta al usuario lo que no puedas deducir del repositorio, en un solo mensaje.
3. Redacta la propuesta con la plantilla de `references/plantilla.md`: como máximo el número configurado de principios, cada uno con ID, una sola frase y una línea `Se verifica:` con un mecanismo concreto (herramienta, métrica y umbral, o revisión). Si un principio no se puede verificar, reformúlalo o descártalo.
4. Muestra la propuesta y espera la aprobación del usuario. No escribas el archivo antes.
5. Cuando el usuario apruebe, escribe `specs/constitution.md` con `Estado: aprobada`.
6. Indica el siguiente paso: especificar una feature con `sdd-spec`.

## Detente si

- El usuario pide principios que se contradicen entre sí: señala la contradicción y pídele que elija.
