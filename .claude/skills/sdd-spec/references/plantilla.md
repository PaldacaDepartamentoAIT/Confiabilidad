# Plantilla: spec.md

```markdown
# Spec: <feature>
Estado: borrador | aprobada

## Objetivo (por qué)

## Requisitos funcionales
### RF-001 <título>
<requisito en EARS>

## Supuestos
- S-01 <supuesto>

## Fuera de alcance

## Criterios de finalización

## Historial de cambios
- <AAAA-MM-DD> — <cambio> — RF: <RF afectados> — Estado: pendiente de clarificar | clarificado | impacto analizado
```

## Patrones EARS

| Patrón | Forma | Ejemplo |
|---|---|---|
| Ubicuo | El sistema deberá … | El sistema deberá registrar la fecha de cada pedido. |
| Evento | Cuando …, el sistema deberá … | Cuando el usuario confirme el pago, el sistema deberá enviar un correo de confirmación. |
| Estado | Mientras …, el sistema deberá … | Mientras la sesión esté bloqueada, el sistema deberá rechazar cualquier operación de escritura. |
| No deseado | Si …, entonces el sistema deberá … | Si el pago es rechazado, entonces el sistema deberá mostrar el motivo y conservar el carrito. |
| Opcional | Donde …, el sistema deberá … | Donde el usuario tenga plan premium, el sistema deberá permitir exportar en PDF. |
