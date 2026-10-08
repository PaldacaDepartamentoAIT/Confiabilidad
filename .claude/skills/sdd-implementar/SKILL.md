---
name: sdd-implementar
description: 'Implementa las tareas de una feature SDD siguiendo TDD (test que falla, implementación mínima, mutante, suite completa) según el modo de aprobación de la spec: en modo fuerte, una sola tarea y se detiene; en modo ligero, encadena todas las tareas con paradas obligatorias, entrega un informe y lanza la validación. También corrige bugs creando antes su tarea de corrección. Usar cuando el usuario quiera implementar, programar o codificar una tarea, continuar con la siguiente tarea, o arreglar un bug en una feature especificada con SDD. No usar para validar la feature completa (sdd-validar).'
---

# SDD · Implementación

Implementa las tareas con TDD. Ver el test fallar antes de implementar demuestra que el test prueba algo real, y matar un mutante demuestra que el test detecta un error. El modo de aprobación de la spec (línea `Aprobación:`, ver `AGENTS.md`) decide cuántas tareas se hacen antes de detenerse:

- **Fuerte** (o sin línea `Aprobación:`): una sola tarea y te detienes. Cada cambio de texto o código se presenta con Aceptar/Rechazar antes de aplicarse.
- **Ligero**: encadenas todas las tareas pendientes sin pedir aprobación de cada diff, y te detienes solo en las paradas obligatorias de `AGENTS.md`.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.
- **ID de la tarea** (`T-XXX`). Si el usuario no lo da, propón la primera tarea sin marcar cuyas dependencias estén marcadas y pide confirmación.
- **Comando de tests**: lee `sdd.comando_tests` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo.

**Bugs:** si el usuario reporta un bug y no hay tarea para él, primero comprueba que el comportamiento esperado ya está en la spec. Si lo está, propón una tarea de corrección con este formato, usando el siguiente ID libre de `tasks.md`; pide aprobación (en ambos modos: es una tarea nueva), añádela y continúa con ella:

```
- [ ] T-0XX Corrección: <título>
  Tipo: corrección | Origen: bug reportado
  RF: RF-00X | Depende de: — | Archivos: <n>
  Causa: <qué falla y por qué, si ya lo sabes>
  Hecho cuando: <el test que reproduce el bug pasa y la suite completa sigue en verde>
```
 Si no lo está, no es un bug sino un cambio: remite a `sdd-cambio`.

## Precondiciones

- [ ] Existe `specs/constitution.md`.
- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] Existe `specs/<feature>/plan.md` con `Estado: aprobado`.
- [ ] Existe `specs/<feature>/tasks.md` con `Estado: aprobado`.
- [ ] La tarea existe y no está marcada.
- [ ] Todas sus dependencias están marcadas.
- [ ] La suite se ejecuta. Ejecútala antes de empezar: si hay tests que ya fallan, no podrías distinguir tus fallos de los anteriores, así que abstente e informa de cuáles fallan.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar la implementación. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento por tarea

1. Lee la constitución, la spec, el plan y la tarea.
2. Escribe los tests de la tarea, ejecútalos y muestra la salida donde FALLAN. Si pasan sin haber implementado nada, el test no prueba el comportamiento nuevo: corrígelo antes de seguir.
3. Implementa lo mínimo necesario para que pasen.
4. Introduce al menos un mutante en el código nuevo (un cambio pequeño que debería romper el comportamiento), ejecuta los tests del archivo afectado y comprueba que alguno falla; después deshaz el mutante. Si sobrevive, añade el test que lo mata dentro de los archivos de la tarea. Si es equivalente (no cambia el comportamiento), anótalo en `Decisiones:`.
5. Ejecuta la suite completa y muestra la salida real. Pasa tipos y lint/formato según «Al terminar cualquier tarea» de `AGENTS.md`.
6. Comprueba la línea `Hecho cuando:` de la tarea.
7. Marca la tarea como hecha en `tasks.md`. Si tomaste decisiones que no están explícitas en la spec ni en el plan (también dentro de los tests), añade bajo la tarea una línea `Decisiones:` con cada una, su motivo, su nivel de confianza ([Cierto]/[Probable]/[Suposición]) y cómo revertirla.
8. Haz un commit atómico de la tarea y súbelo (ver «Commits» en `AGENTS.md`).

## Modo fuerte

Tras el paso 8, informa con este formato y DETENTE; no empieces la siguiente tarea aunque sea obvia:

```
Tarea T-XXX completada
Archivos modificados: <lista>
Tests nuevos: <lista>
Mutantes: <muertos / supervivientes y por qué>
Suite: <n> pasan, <n> fallan
Siguiente tarea disponible: <T-XXX | ninguna: ejecuta sdd-validar>
```

## Modo ligero

1. Tras el paso 8, sigue con la siguiente tarea sin marcar cuyas dependencias estén marcadas, hasta que no quede ninguna.
2. Ante una parada obligatoria de `AGENTS.md`, detente: explica la causa, la tarea en curso y las opciones, y espera al usuario. Cuando la resuelva, continúa la cadena sin volver a preguntar el modo.
3. Al terminar todas las tareas, entrega el informe con el formato de abajo y lanza `sdd-validar` en un subagente sin el contexto de esta conversación. Si el entorno no admite subagentes, no valides aquí: pide al usuario que la lance en una sesión nueva.
4. Si el veredicto es CUMPLIDA, `sdd-validar` registra la validación y el resumen; actualiza el informe con el resultado. Con cualquier otro veredicto, detente: las tareas de corrección y el cierre con riesgo residual los decide el usuario.
5. Termina preguntando si abres el PR; no lo abras sin su confirmación.

```
# Informe: <feature>

## Tareas hechas
- T-XXX <título> — <commit>

## Decisiones que tomé
- <decisión> — Motivo: <…> — Confianza: [Cierto|Probable|Suposición] — Cómo revertirla: <…> (T-XXX)

## Mutantes supervivientes, riesgos y huecos de tests
- <…>

## Textos escritos sin aprobación previa
- <archivo> — <qué cambió>

## Estado
Suite: <n> pasan, <n> fallan · Cobertura: <n %> · mypy/ruff/black: <limpio | errores>
Validación: <pendiente | CUMPLIDA | NO CUMPLIDA: resumen>
```

## Detente sin implementar si

En ambos modos (en modo ligero son paradas obligatorias):

- La tarea exige cambiar la spec: explícalo y remite a `sdd-cambio`.
- La tarea exige cambiar el plan o tocar un módulo fuera de su alcance: explícalo y remite a `sdd-plan`.
- La tarea obliga a violar un principio de la constitución: indica cuál.
- Necesitas tocar más archivos de los previstos y la tarea no tiene una `Excepción:` que lo cubra: explica por qué y deja que el usuario decida.
