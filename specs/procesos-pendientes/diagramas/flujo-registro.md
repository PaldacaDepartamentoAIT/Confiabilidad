# Flujo de registro (Mermaid)

Versión en texto del [diagrama original](flujo-registro.png), ajustada a la spec aprobada. Los
cambios respecto a la imagen están en la sección final.

```mermaid
flowchart TD
    A([Inicio]) --> B[Rellena el formulario de registro]
    B --> C{¿Datos válidos?}
    C -- No --> C1[Muestra el error de cada campo] --> B
    C -- Sí --> D{¿El correo ya tiene cuenta?}
    D -- Sí --> D1([Cuenta existente: no se guarda nada])
    D -- No --> E{¿Hay un registro pendiente vigente con ese correo?}
    E -- Sí --> E1["Conserva sus datos y descarta los nuevos;<br/>nuevo public_id, nuevo código,<br/>intentos a 0, validación anulada"]
    E -- No --> E2["Borra los caducados de ese correo;<br/>guarda el registro pendiente<br/>con public_id y código (15 min)"]
    E1 --> F
    E2 --> F[Entrega el código y el public_id]
    F --> G[Introduce el código]
    G --> H{¿Proceso caducado?<br/>código caducado + 15 min de gracia,<br/>o 1 h desde el alta}
    H -- Sí --> X([Caducado: hay que empezar de nuevo])
    H -- No --> I{¿5 intentos fallidos?}
    I -- Sí --> R
    I -- No --> J{¿Código vigente?}
    J -- No --> R[Reenvía el código: mismo public_id,<br/>código nuevo, intentos a 0]
    R -.->|límite de frecuencia: fuera de alcance, S-01| G
    J -- Sí --> K{¿Código correcto?}
    K -- No --> K1[Suma un intento fallido] --> G
    K -- Sí --> L[Código validado]
    L -. se puede cerrar y reanudar con el public_id<br/>mientras el proceso siga vigente .-> M
    L --> M[Introduce la contraseña]
    M --> N{¿Proceso caducado?}
    N -- Sí --> X
    N -- No --> O{¿El correo consiguió cuenta entretanto?}
    O -- Sí --> O1([Rechazado: se borra el registro pendiente])
    O -- No --> P{¿Contraseña válida?<br/>12+ caracteres, no parecida al correo<br/>ni al nombre, no común, no filtrada}
    P -- No --> P1[Muestra cada regla incumplida] --> M
    P -- Sí --> Q([FIN: se crea la cuenta con el correo verificado<br/>y se borra el registro pendiente])
```

## Cambios respecto al diagrama original
- La comprobación de cuenta existente va después de validar los datos: si fuera antes, la
  respuesta revelaría qué correos tienen cuenta.
- Se añaden los intentos fallidos y el bloqueo (RF-010), la vida máxima de 1 hora (RF-011), el
  registro repetido (RF-005) y el caso de cuenta creada entretanto (RF-012).
- El límite de frecuencia del reenvío queda fuera de esta feature (S-01).
- Los tiempos y el número de intentos son los valores por defecto; se ajustan por configuración
  (RF-019).
