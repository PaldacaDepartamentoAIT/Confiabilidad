---
name: sdd-clarificar
description: 'Revisa una spec SDD como un QA profesional para detectar ambigüedades, contradicciones, casos límite ausentes, requisitos no verificables y conflictos con la constitución, incorpora las respuestas del usuario, determina el nivel de riesgo y validación requerido y aprueba la spec. Usar cuando el usuario quiera revisar, clarificar, validar o aprobar una spec, cuando se acaba de crear una spec con sdd-spec o cuando se acaba de cambiar una con sdd-cambio. No usar para verificar código (sdd-validar).'
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
3. No edites la spec ni recomiendes soluciones: el usuario debe decidir sin que una respuesta sugerida condicione su criterio.
4. Presenta los hallazgos con el formato de `references/plantilla.md`, ordenados por gravedad, en el propio mensaje.
5. Después, pide la respuesta de cada hallazgo en formato de selección, con la herramienta de
   preguntas de opción múltiple (hasta 4 hallazgos por llamada, en orden de gravedad):
   - De 2 a 4 opciones excluyentes que cubran las respuestas razonables, cada una con una
     descripción breve de su consecuencia. Ninguna se marca como recomendada ni se ordena por
     preferencia (paso 3).
   - El usuario siempre puede escribir otra respuesta; trátala igual que una opción elegida.
   - Este formato es solo para responder hallazgos y elegir el nivel de validación: el diff y la
     aprobación de la spec (pasos 3 y 5 de la fase B) se piden en texto, según `AGENTS.md`.
6. Si no hay hallazgos, dilo y pasa directamente al paso 4 de la fase B para determinar el nivel de riesgo y validación y pedir la aprobación.

### Fase B: cierre

1. Espera las respuestas del usuario. Si alguna no resuelve su hallazgo, dilo y vuelve a preguntar solo por ese.
2. Prepara los cambios en la spec: modifica los RF afectados sin cambiar sus IDs, añade los nuevos con el siguiente ID libre y registra cada cambio en el historial.
3. Muestra el diff y espera la aprobación del usuario antes de escribir.
4. **Nivel de riesgo y validación** (obligatorio en feature nueva, y tras un cambio si varía el alcance o el riesgo): analiza lo clarificado frente a los criterios de riesgo y explica brevemente por qué corresponde ese nivel. Después pregunta al usuario qué nivel de validación aplicar mediante la herramienta de preguntas de opción múltiple, colocando **en primer lugar** y con **`(Recomendada)`** al final la opción indicada según el riesgo (a diferencia de la Fase A, aquí sí se recomienda explícitamente la opción adecuada):
   - **Validación estricta (Obligatoria)**: Solo para el core del negocio, flujos de dinero/datos críticos, cambios en esquemas de base de datos o contratos de API pública. Aquí un error sale carísimo.
   - **Validación ligera / asíncrona**: Para features secundarios o internos. Se escribe una spec mínima (criterios de aceptación en bullets, sin diagramas extensos) y la validación ocurre en el Code Review o mediante tests automatizados básicos.
   - **Sin SDD (Vía rápida)**: Hotfixes, ajustes visuales de UI, refactors internos que no alteran comportamiento o prototipos desechables.

   Registra la elección debajo de `Aprobación:` con `Validación: estricta | ligera | sin-sdd`. Si el usuario elige `ligera`, simplifica o confirma la spec en formato mínimo (criterios de aceptación en bullets, sin diagramas extensos); si elige `sin-sdd`, anótalo en el historial de la spec.
5. Pide al usuario que apruebe la spec (incluyendo el cambio de la línea `Validación:` en texto si no estaba aprobada). Cuando lo haga, cambia a `Estado: aprobada` y, en modo tras un cambio, marca la entrada del historial como `clarificado`.
6. Indica el siguiente paso según el nivel de validación elegido y el modo:
   - Si `Validación: estricta`: `sdd-plan` para una feature nueva, o `sdd-cambio` (análisis de impacto) tras un cambio.
   - Si `Validación: ligera`: si es feature nueva, pasar directamente a implementación con tests automatizados básicos (o `sdd-tareas` breves) y validación en Code Review (sin `sdd-plan` extenso ni `sdd-validar` en subagente); tras un cambio, `sdd-cambio` (análisis de impacto).
   - Si `Validación: sin-sdd`: continuar directamente por vía rápida en la rama adecuada (`fix/`, `refactor/`, `style/`, `poc/`) cumpliendo los checks de código y Code Review en PR, sin ejecutar `sdd-plan`, `sdd-tareas` ni `sdd-validar`.

## Detente si

- Resolver un hallazgo exige contradecir la constitución: dilo y pregunta al usuario si quiere revisar la constitución con `sdd-constitucion`.
