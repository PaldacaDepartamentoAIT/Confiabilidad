# Spec: desktop-tauri-seguro
Estado: borrador
Aprobación: ligera

## Objetivo (por qué)
La aplicación de escritorio envuelve la app web. Hoy no restringe de dónde se cargan los recursos
y concede a la interfaz permisos nativos que no usa. Si alguien consiguiera inyectar un script
(por una dependencia comprometida o un contenido malicioso), podría ejecutarlo dentro de la app y
usar esos permisos sobre el equipo del usuario. Esta feature deja la aplicación de escritorio
lista para crecer: solo ejecuta código de la propia app, solo se conecta con el backend
configurado, no concede permisos nativos y arranca en Linux, Windows y macOS.

## Requisitos funcionales
### RF-001 Scripts solo de la propia app
La aplicación de escritorio deberá ejecutar únicamente scripts que formen parte de la propia app.

### RF-002 Rechazo de scripts ajenos
Si la interfaz intenta cargar o ejecutar un script que no forma parte de la propia app (de un
origen externo o insertado en línea), entonces la aplicación de escritorio deberá bloquearlo.

### RF-003 Resto de recursos solo de la propia app
La aplicación de escritorio deberá cargar estilos, fuentes, imágenes y demás recursos únicamente
desde la propia app.

### RF-004 Conexiones solo con la app y el backend
La aplicación de escritorio deberá permitir conexiones de red (peticiones HTTP y WebSocket)
únicamente con la propia app y con el origen configurado del backend, y bloquear cualquier otra.

### RF-005 Sin permisos nativos
La aplicación de escritorio deberá conceder cero permisos nativos a la interfaz.

### RF-006 Misma política en desarrollo
Mientras la aplicación de escritorio se ejecute en modo de desarrollo, deberá aplicar la misma
política de RF-001 a RF-004, ampliada solo con el origen local del servidor de desarrollo.

### RF-007 Navegación restringida a la propia app
Si la ventana intenta navegar a un origen distinto de la propia app, entonces la aplicación de
escritorio deberá impedir esa navegación y seguir mostrando la app.

### RF-008 Compilación en los tres sistemas operativos
Cuando se integre un cambio, el sistema de integración continua deberá compilar la aplicación de
escritorio en Linux, Windows y macOS, y fallar si alguna compilación falla.

### RF-009 Arranque en los tres sistemas operativos
La aplicación de escritorio deberá arrancar y mostrar la interfaz web sin violaciones de la
política de seguridad en Linux, Windows y macOS.

## Supuestos
- S-01 La interfaz actual no usa ninguna función nativa de escritorio, por lo que retirar todos
  los permisos no rompe nada. Cada feature futura que necesite uno lo añadirá y lo justificará.
- S-02 El backend se sirve desde un único origen configurable (el mismo para HTTP y WebSocket).
- S-03 La comprobación de RF-009 es manual: una persona arranca la aplicación en cada sistema
  operativo y revisa que la interfaz carga sin errores de la política. Se anota en el
  `HUMAN_TODO.md` de la feature.

## Fuera de alcance
- Abrir enlaces externos en el navegador del sistema.
- Firma de código, notarización e instaladores distribuibles.
- Actualizaciones automáticas.
- Versiones móviles.
- Conectar la interfaz con el backend (solo se permite la conexión; no se implementa ninguna
  llamada).

## Criterios de finalización
- RF-001 a RF-008 verificados con evidencia automatizada en la integración continua.
- RF-009 comprobado a mano en Linux, Windows y macOS y marcado en el `HUMAN_TODO.md` de la feature.
- La configuración de la aplicación de escritorio no concede ningún permiso nativo.

## Historial de cambios
- 2026-11-05 — Creación de la spec — RF: RF-001 a RF-009 — Estado: pendiente de clarificar
