# Plantilla: tasks.md

```markdown
# Tareas: <feature>
Estado: borrador | aprobado

- [ ] T-001 <título>
  RF: RF-001 | Depende de: — | Archivos: <n>
  Hecho cuando: <test o comando concreto que pasa>
  Excepción: <solo si supera el límite de archivos, y por qué>

## Entregas
- E-01 <qué puede probar el usuario cuando se fusione>
  Tareas: T-001, T-002 | Líneas estimadas: <n> | Rama: <tipo>/<feature>-<descripcion>
  Cómo probarlo: <comando o pasos concretos>
  Excepción: <solo si supera sdd.max_lineas_pr, y por qué>

## RF sin tarea
<ninguno | lista>
```

Las tareas de corrección que añade `sdd-validar` o `sdd-implementar` (bugs) usan este formato:

```markdown
- [ ] T-0XX Corrección: <título>
  Tipo: corrección | Origen: <validación de RF-00X | bug reportado>
  RF: RF-00X | Depende de: — | Archivos: <n>
  Causa: <resumen del diagnóstico>
  Hecho cuando: <el test que reproduce el fallo pasa y la suite completa sigue en verde>
```
