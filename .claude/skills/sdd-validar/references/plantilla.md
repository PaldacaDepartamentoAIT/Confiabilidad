# Formato del informe de validación

```markdown
# Validación: <feature>

Suite: <n> pasan, <n> fallan (salida completa arriba)

| RF | Test | Aserción que lo verifica | Resultado |
|---|---|---|---|

Criterios de finalización: <cumplidos / pendientes>
Veredicto: CUMPLIDA | NO CUMPLIDA
RF pendientes: <lista>

## Diagnóstico de fallos
### RF-00X
Síntoma: <qué falla, con la salida real>
Causa: <por qué, con archivo y parte responsable>
Origen: Código | Test | Plan | Spec
Acción: <tarea propuesta | fase a repetir y motivo>

## Tareas de corrección propuestas
- [ ] T-0XX Corrección: <título>
  Tipo: corrección | Origen: validación de RF-00X
  RF: RF-00X | Depende de: — | Archivos: <n>
  Causa: <resumen del diagnóstico>
  Hecho cuando: <el test que reproduce el fallo pasa y la suite completa sigue en verde>
```

## Siguiente paso según el origen

| Origen | Siguiente paso |
|---|---|
| Código o Test | Aprobar las tareas de corrección → `sdd-implementar` → `sdd-validar` en sesión nueva |
| Plan | `sdd-plan` → `sdd-tareas` → `sdd-implementar` → `sdd-validar` |
| Spec | `sdd-cambio` |
