# Spec: desktop-tauri-seguro
Estado: aprobada
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
desde los archivos de la propia app, con dos excepciones: las imágenes y los archivos de descarga
que la propia app genere en memoria. Los estilos insertados en línea se bloquean igual que los
scripts.

### RF-004 Conexiones solo con la app y el backend
La aplicación de escritorio deberá permitir conexiones de red (peticiones HTTP y WebSocket)
únicamente con la propia app y con el origen del backend definido al compilarla, que será el
mismo que usa la interfaz para llamar al backend, y bloquear cualquier otra.

### RF-005 Sin permisos nativos
La aplicación de escritorio deberá conceder cero permisos nativos a la interfaz.

### RF-006 Misma política en desarrollo
Mientras la aplicación de escritorio se ejecute en modo de desarrollo, deberá aplicar la misma
política de RF-001 a RF-004, ampliada solo con el origen local del servidor de desarrollo y con un
identificador fijo (nonce) que autoriza únicamente los scripts y estilos en línea que
inserta el propio servidor de desarrollo. Cualquier otro script o estilo en línea se seguirá
bloqueando, y la política de producción no incluirá ese identificador.

### RF-007 Navegación restringida a la propia app
Si la ventana intenta navegar a un origen distinto de la propia app, incluido el del backend,
entonces la aplicación de escritorio deberá impedir esa navegación sin avisar al usuario y seguir
mostrando la pantalla en la que estaba.

### RF-008 Compilación en los tres sistemas operativos
Cuando un cambio toque `desktop/` o `frontend/`, el sistema de integración continua deberá
compilar el ejecutable de la aplicación de escritorio (sin instaladores) en Linux, Windows y macOS,
y fallar si alguna compilación falla.

### RF-009 Arranque en los tres sistemas operativos
La compilación de depuración de la aplicación de escritorio deberá arrancar en Linux, Windows y
macOS, mostrar la interfaz web completa y no registrar ninguna violación de la política de
seguridad en la consola de las herramientas de desarrollo.

### RF-010 Backend no definido al compilar
Si no se define el origen del backend al compilar, ni en el entorno ni en los archivos de
configuración que la interfaz carga al compilar en producción, entonces la aplicación de escritorio
deberá compilar igualmente y permitir conexiones de red únicamente con la propia app.

### RF-011 Descarga de archivos generados por la app
Cuando la interfaz ofrezca al usuario un archivo que la propia app ha generado en memoria, la
aplicación de escritorio deberá permitir guardarlo en el equipo en Linux, Windows y macOS.

### RF-012 Configuración del backend incoherente
Si la configuración del backend que usará la interfaz (la del entorno y la de los archivos de
configuración que la interfaz carga al compilar en producción, con la misma prioridad con la que los
aplica) no coincide con la que recibe la política de seguridad al compilar, entonces la compilación de la aplicación de escritorio deberá fallar e
indicar la discrepancia.

## Supuestos
- S-01 La interfaz actual no usa ninguna función nativa de escritorio, por lo que retirar todos
  los permisos no rompe nada. Cada feature futura que necesite uno lo añadirá y lo justificará.
- S-02 El backend se sirve desde un único origen (el mismo para HTTP y WebSocket). Se define al
  compilar con un valor distinto por entorno, en la misma configuración con la que la interfaz
  construye sus llamadas al backend, que puede incluir una ruta.
- S-03 Las comprobaciones de RF-009 y RF-011 son manuales: en cada sistema operativo, una persona
  arranca la compilación de depuración, revisa la consola y guarda un archivo generado por la app.
  Se anotan en el `HUMAN_TODO.md` de la feature.

## Fuera de alcance
- Abrir enlaces externos en el navegador del sistema.
- Firma de código, notarización e instaladores distribuibles.
- Actualizaciones automáticas.
- Versiones móviles.
- Cambiar cómo la interfaz llama al backend: ya existe en `main` y esta feature solo lo permite y
  lo restringe.

## Criterios de finalización
- RF-001 a RF-008 y RF-010 verificados en la integración continua con dos tipos de evidencia: un
  test que comprueba la configuración (directivas de la política y ausencia de permisos) y un test
  que arranca la app y comprueba su comportamiento (bloqueo de scripts ajenos, de conexiones a
  otros orígenes y de la navegación externa).
- RF-009 y RF-011 comprobados a mano en Linux, Windows y macOS y marcados en el `HUMAN_TODO.md` de
  la feature.
- La configuración de la aplicación de escritorio no concede ningún permiso nativo.

## Historial de cambios
- 2026-11-05 — Creación de la spec — RF: RF-001 a RF-009 — Estado: impacto analizado
- 2026-11-05 — Clarificación C-01 a C-07 — RF: RF-003, RF-004, RF-007, RF-008, RF-009, RF-010, RF-011 — Estado: impacto analizado
- 2026-11-05 — En desarrollo se permite un nonce fijo para lo que inserta el servidor de desarrollo — RF: RF-006 — Estado: impacto analizado
- 2026-11-06 — Una sola configuración del backend para la interfaz y la política — RF: RF-004, RF-010, RF-012 — Estado: clarificado
