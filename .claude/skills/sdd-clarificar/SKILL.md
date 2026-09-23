---
name: sdd-clarificar
description: 'Revisa una spec SDD como un QA profesional para detectar ambigüedades, contradicciones, casos límite ausentes, requisitos no verificables y conflictos con la constitución, y después incorpora las respuestas del usuario y aprueba la spec. Usar cuando el usuario quiera revisar, clarificar, validar o aprobar una spec, cuando se acaba de crear una spec con sdd-spec o cuando se acaba de cambiar una con sdd-cambio. No usar para verificar código (sdd-validar).'
---

# SDD · Clarificación

Encuentra los huecos de la spec antes de diseñar nada: un error aquí se corrige en minutos y en el código cuesta horas. Solo detectas problemas; las respuestas las da el usuario porque son decisiones de negocio.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.

Si falta, pídelo al usuario y no continúes hasta tenerlo.

## Precondiciones

- [ ] Existe `specs/constitution.md`.
- [ ] Existe `specs/<feature>/spec.md`.
- [ ] La spec está en `Estado: borrador`. Si está aprobada y no hay ninguna entrada del historial con estado `pendiente de clarificar`, no hay nada que clarificar: el siguiente paso es `sdd-plan`, o `sdd-cambio` si hay un requisito nuevo.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar la clarificación. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Modo

Determínalo leyendo la spec e indícaselo al usuario:

- **Tras un cambio**: el historial tiene una entrada con `Estado: pendiente de clarificar`. Revisa solo los RF de esa entrada y su relación con el resto de la spec.
- **Feature nueva**: en cualquier otro caso. Revisa la spec completa.

## Procedimiento

### Fase A: detección

1. Lee la constitución y la spec.
2. Busca ambigüedades, contradicciones entre RF, casos límite ausentes, RF no verificables y conflictos con la constitución, dentro del alcance del modo.
3. No edites la spec ni propongas soluciones: el usuario debe decidir sin que una respuesta sugerida condicione su criterio.
4. Presenta los hallazgos con el formato de `references/plantilla.md`, ordenados por gravedad.
5. Si no hay hallazgos, dilo y pasa directamente al paso 4 de la fase B para pedir la aprobación.

### Fase B: cierre

1. Espera las respuestas del usuario. Si alguna no resuelve su hallazgo, dilo y vuelve a preguntar solo por ese.
2. Prepara los cambios en la spec: modifica los RF afectados sin cambiar sus IDs, añade los nuevos con el siguiente ID libre y registra cada cambio en el historial.
3. Muestra el diff y espera la aprobación del usuario antes de escribir.
4. Pide al usuario que apruebe la spec. Cuando lo haga, cambia a `Estado: aprobada` y, en modo tras un cambio, marca la entrada del historial como `clarificado`.
5. Indica el siguiente paso: `sdd-plan` para una feature nueva, o `sdd-cambio` (análisis de impacto) tras un cambio.

## Detente si

- Resolver un hallazgo exige contradecir la constitución: dilo y pregunta al usuario si quiere revisar la constitución con `sdd-constitucion`.
