---
name: sdd-validar
description: 'Valida que el código de una feature SDD cumple su spec requisito a requisito, con evidencia de la suite de tests, diagnostica cada fallo (síntoma, causa y origen: código, test, plan o spec) y propone tareas de corrección. Usar cuando el usuario quiera validar, verificar o comprobar si una feature está terminada, si cumple la spec, o cuando se han completado todas las tareas. No usar para revisar la spec antes de implementar (sdd-clarificar).'
---

# SDD · Validación

Comprueba con evidencia que el código cumple la spec. Que los tests pasen no basta: un test puede existir y no probar lo que dice el requisito.

## Datos necesarios

- **Feature**: nombre de la carpeta en `specs/`.
- **Comando de tests**: lee `sdd.comando_tests` en la sección SDD de `CLAUDE.md` o `AGENTS.md`.

Si falta alguno, pídelo al usuario en un solo mensaje y no continúes hasta tenerlo.

## Contexto limpio

El agente que implementó tiende a darse la razón a sí mismo. Si en esta conversación se ha implementado código de esta feature, adviértelo al usuario y recomiéndale una sesión nueva. Si el entorno permite subagentes, ejecuta la validación en uno sin el contexto previo. Continúa en esta sesión solo si el usuario lo confirma.

## Precondiciones

- [ ] Existe `specs/<feature>/spec.md` con `Estado: aprobada`.
- [ ] Existen `specs/<feature>/plan.md` y `specs/<feature>/tasks.md`.
- [ ] Todas las tareas de `tasks.md` están marcadas.
- [ ] La suite se ejecuta con el comando configurado.

## Si falta una precondición

No crees, edites ni borres ningún archivo. Responde solo con:

```
No puedo ejecutar la validación. Faltan estas precondiciones:
- ✗ <precondición> — <qué encontraste>
Siguiente paso: <skill a ejecutar o acción del usuario>
```

## Procedimiento

1. Lee la spec, el plan y las tareas.
2. Ejecuta la suite completa y muestra la salida real.
3. Recorre la spec RF por RF (sin los obsoletos). Para cada uno indica el test que lo cubre, la aserción concreta que verifica lo que dice el RF y su resultado. Lee el código del test: no te fíes de su nombre.
   - CUMPLIDO: existe una aserción que prueba exactamente el comportamiento del RF y pasa.
   - NO CUMPLIDO: no hay test, el test no prueba el RF o el test falla.
4. Verifica los criterios de finalización.
5. Para cada RF NO CUMPLIDO, diagnostica síntoma, causa y origen con el formato de `references/plantilla.md`:
   - *Código*: la implementación no hace lo que dice el RF.
   - *Test*: falta el test o no prueba lo que dice el RF.
   - *Plan*: el diseño no permite cumplir el RF.
   - *Spec*: el RF es ambiguo, contradictorio o imposible de cumplir.
6. Si el origen es *Código* o *Test*, propón una tarea de corrección con el siguiente ID libre de `tasks.md`. Si es *Plan* o *Spec*, no propongas tarea: indica que hay que volver a `sdd-plan` o a `sdd-cambio` y por qué. Una tarea no arregla un diseño o un requisito equivocados; solo los tapa.
7. No modifiques código ni archivos durante el diagnóstico. Muestra el informe y espera la aprobación del usuario.
8. Cuando el usuario apruebe las tareas de corrección, añádelas a `tasks.md`. Si el veredicto es CUMPLIDA, añade al historial de la spec una entrada `Validación: CUMPLIDA` con la fecha.
9. Indica el siguiente paso según el origen de los fallos (ver la tabla de `references/plantilla.md`).
