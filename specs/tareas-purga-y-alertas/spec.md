# Spec: tareas-purga-y-alertas
Estado: aprobada
Aprobación: ligera
Validación: estricta

## Objetivo (por qué)
El sistema ya cuenta con lógica de depuración para registros de acceso pendientes, sesiones caducadas y eventos de seguridad de auditoría, pero la depuración de auditoría aún requiere ejecución manual y ninguna de las tres tareas periódicas deja constancia estructurada de su última ejecución ni avisa cuando falla. Sin visibilidad ni alertas, un fallo silencioso en las tareas de limpieza puede acumular datos obsoletos o incumplir los plazos de conservación sin que el equipo operativo lo detecte a tiempo. Esta feature unifica la ejecución autónoma de las tres tareas, registra el resultado de la última ejecución de cada una y genera alertas verificables ante cualquier fallo.

## Requisitos funcionales

### RF-001 Ejecución automática de las tres tareas de depuración
Mientras el planificador periódico y el trabajador en segundo plano estén activos, el sistema deberá ejecutar automáticamente sin intervención manual las tareas de purga de registros pendientes, limpieza de sesiones caducadas y depuración de eventos de auditoría.

### RF-002 Frecuencias configurables de programación
El sistema deberá programar por defecto cada hora la purga de registros pendientes y la limpieza de sesiones caducadas, y una vez al día la depuración de eventos de auditoría, permitiendo ajustar el intervalo de cada tarea mediante configuración del entorno (incluidos intervalos cortos en pruebas o desarrollo para verificar el disparo autónomo sin esperar al ciclo estándar ni editar código).

### RF-003 Preservación de reglas vigentes de retención y protección
Cuando se ejecute cualquiera de las tres tareas periódicas, el sistema deberá aplicar los mismos criterios de retención, plazos y salvaguardas de borrado ya definidos para cada dominio (registros pendientes vencidos tras el periodo de conservación, sesiones caducadas y eventos de auditoría con más de un año conservando su protección de solo inserción frente a accesos no autorizados).

### RF-004 Registro de la última ejecución por tarea
Las ejecuciones de una misma tarea periódica deberán serializarse en orden para evitar solapamientos. Antes de la primera ejecución no existirá registro de estado para esa tarea; cuando finalice (con éxito o con fallo) cualquiera de las tres tareas periódicas, el sistema deberá guardar en un único registro de estado para esa tarea la fecha y hora de inicio, la fecha y hora de finalización, el resultado (éxito o fallo), el número de registros depurados y el resumen del error si falló (tipo y mensaje de excepción truncado, sin trazas completas ni secretos), sobrescribiendo los datos de la ejecución anterior de esa misma tarea.

### RF-005 Generación inmediata de alerta ante fallo
Si la ejecución de cualquiera de las tres tareas periódicas falla por una excepción o error no controlado, entonces el sistema deberá registrar el fallo sin reintentos silenciosos que lo oculten, crear una alerta persistente en el sistema con la tarea afectada, la marca temporal y el resumen truncado del error (tipo y mensaje de excepción), emitir un registro de error con la traza completa en los logs del servidor y enviar un correo de alerta (con el resumen truncado, sin traza completa) a la lista configurada de destinatarios operativos únicamente si no existe ya una alerta abierta previa para esa tarea (en fallos consecutivos se registra cada alerta persistente, pero se suprime el envío repetido de correos mientras siga abierta). Si la base de datos no estuviera disponible al intentar guardar el registro o la alerta, entonces el sistema deberá registrar ambos errores en los logs del servidor sin intentar enviar el correo de alerta.

### RF-006 Resiliencia de la alerta ante incidencias del canal de correo
Si el envío del correo operativo de alerta falla o no hay destinatarios configurados, entonces el sistema deberá conservar igualmente el registro de última ejecución fallida, la alerta persistente en el sistema y la entrada de error en los logs del servidor, dejando constancia en los logs de cualquier error ocurrido al intentar enviar el correo.

### RF-007 Resolución automática de alertas al recuperarse la tarea
Cuando una tarea periódica que tenga alertas abiertas finalice con éxito en una ejecución posterior, el sistema deberá actualizar su registro de última ejecución a éxito y marcar como resueltas sus alertas abiertas registrando la fecha y hora de resolución.

### RF-008 Consulta en el panel de administración interno
El sistema deberá permitir a operadores autorizados consultar, desde el panel de administración interno, el estado de la última ejecución de cada una de las tres tareas y el listado de alertas generadas con su estado (abierta o resuelta) y el detalle del error.

### RF-009 Operación, consulta y fallo simulado desde consola (CLI)
El sistema deberá permitir desde consola (CLI) ejecutar manualmente cada una de las tres tareas, consultar el estado de su última ejecución y sus alertas, y lanzar cualquiera de las tres tareas en modo de fallo simulado controlado sin modificar el código fuente; la simulación deberá encolarse y ejecutarse a través del trabajador asíncrono real y provocar el fallo antes de eliminar ningún registro real, para comprobar de extremo a extremo que se registra el fallo y se genera la alerta.

## Supuestos
- S-01 La lista de destinatarios operativos para alertas por correo se define por configuración del entorno; si está vacía, se omite el envío por correo sin considerarlo un fallo adicional.
- S-02 La simulación de fallo solo puede invocarse de forma explícita desde la consola de operación del servidor o en pruebas automatizadas, y nunca queda expuesta como opción HTTP pública ni de usuario final.

## Fuera de alcance
- Pantallas, avisos o endpoints en la aplicación web de usuarios o en el cliente de escritorio.
- Almacenamiento de un historial completo de todas las ejecuciones pasadas de cada tarea (solo se conserva la última ejecución por tarea y las alertas de fallo).
- Integraciones de alerta con canales externos distintos del correo electrónico operativo (webhooks, mensajería instantánea o plataformas de monitorización externas).
- Cambios en las reglas de negocio o plazos de retención que determinan qué registros pendientes, sesiones o eventos de auditoría se eliminan.

## Criterios de finalización
- Las tres tareas periódicas (purga de registros pendientes, limpieza de sesiones caducadas y depuración de eventos de auditoría) están activas en el planificador y se demuestra con planificador y trabajador reales (reduciendo los intervalos por configuración en pruebas/desarrollo) que las tres se ejecutan solas sin intervención manual.
- Las ejecuciones de una misma tarea se serializan sin pisarse y cada ejecución finalizada actualiza el registro de última ejecución de la tarea correspondiente (inicio, fin, resultado, cantidad depurada y tipo/mensaje de error truncado si aplica), consultable en el panel interno y desde consola.
- Un fallo simulado lanzado desde consola corre en el trabajador asíncrono, falla antes de borrar datos reales, deja la última ejecución en fallo, genera una alerta abierta persistente, escribe la traza completa en el log de errores y envía el correo operativo en el primer fallo cuando existen destinatarios configurados (suprimiendo correos repetidos mientras siga abierta, y registrando solo en logs si falla la base de datos).
- Una ejecución exitosa posterior de la misma tarea actualiza el estado a éxito y cierra automáticamente sus alertas abiertas.
- La suite de pruebas automatizadas, la comprobación de tipos y el análisis de lint/formato pasan sin errores.

## Historial de cambios
- 2026-11-23 — Creación inicial de la spec tras entrevista — RF: RF-001 a RF-009 — Estado: pendiente de clarificar
- 2026-11-23 — Clarificación (C-01 a C-06): fallo simulado en trabajador sin borrar datos, serialización por tarea, alerta por fallo con correo solo en el primer fallo abierto, caída de BD solo en logs, resumen truncado en alerta/correo y verificación con intervalo reducido — RF: RF-002, RF-004, RF-005, RF-009 — Estado: clarificado
