---
name: sdd-implementar
description: 'Implementa una sola tarea de una feature SDD siguiendo TDD (test que falla, implementación mínima, suite completa), la marca como hecha y se detiene. También corrige bugs creando antes su tarea de corrección. Usar cuando el usuario quiera implementar, programar o codificar una tarea, continuar con la siguiente tarea, o arreglar un bug en una feature especificada con SDD. No usar para validar la feature completa (sdd-validar).'
---

# SDD · Implementación

Implementa una sola tarea y detente. Ver el test fallar antes de implementar demuestra que el test prueba algo real, y detenerse tras cada tarea le da al usuario un punto de control después de cada paso.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.
- **ID de la tarea** (`T-XXX`). Si el usuario no lo da, propón la primera tarea sin marcar cuyas dependencias estén marcadas y pide confirmación.
- **Comando de tests**: lee `sdd.comando_tests` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo.

**Bugs:** si el usuario reporta un bug y no hay tarea para él, primero comprueba que el comportamiento esperado ya está en la spec. Si lo está, propón una tarea de corrección con este formato, usando el siguiente ID libre de `tasks.md`; pide aprobación, añádela y continúa con ella:

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

## Procedimiento

1. Lee la constitución, la spec, el plan y la tarea.
2. Escribe los tests de la tarea, ejecútalos y muestra la salida donde FALLAN. Si pasan sin haber implementado nada, el test no prueba el comportamiento nuevo: corrígelo antes de seguir.
3. Implementa lo mínimo necesario para que pasen.
4. Ejecuta la suite completa y muestra la salida real.
5. Comprueba la línea `Hecho cuando:` de la tarea.
6. Marca la tarea como hecha en `tasks.md`.
7. Informa con este formato y DETENTE; no empieces la siguiente tarea aunque sea obvia:

```
Tarea T-XXX completada
Archivos modificados: <lista>
Tests nuevos: <lista>
Suite: <n> pasan, <n> fallan
Siguiente tarea disponible: <T-XXX | ninguna: ejecuta sdd-validar>
```

## Detente sin implementar si

- La tarea exige cambiar la spec: explícalo y remite a `sdd-cambio`.
- La tarea exige cambiar el plan o tocar un módulo fuera de su alcance: explícalo y remite a `sdd-plan`.
- La tarea obliga a violar un principio de la constitución: indica cuál.
- Necesitas tocar más archivos de los previstos y la tarea no tiene una `Excepción:` que lo cubra: explica por qué y deja que el usuario decida.
