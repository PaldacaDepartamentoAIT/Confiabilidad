# Resumen — consentimientos
Estado: implementada, pendiente de validación · Última actualización: 2026-10-07

## Qué se hizo
El sistema guarda los textos legales versionados y la prueba de quién los aceptó y cuándo, aunque
después se borre la cuenta. Todo vive en la app nueva `apps/consents`, se gestiona desde el panel
de administración de Django y se puede recorrer desde consola con `manage.py consents`, sin frontend
ni API (RF-016). La API futura usará el mismo servicio (`apps/consents/services.py`).

- **Documentos legales** (`Terms`, que guarda los dos tipos): términos de uso y texto de marketing,
  con contenido en Markdown sin HTML, versión (1–20 caracteres: letras, dígitos, `.` y `-`), idioma
  (`es`, `pt-BR` o `en`), si exige nueva aceptación y una fecha de publicación opcional (sin ella
  es un borrador). No puede haber dos con el mismo tipo, idioma y versión, sin distinguir
  mayúsculas: "V1" = "v1" (RF-001, RF-002).
- **Versión vigente**: una versión entra en vigor cuando sus **tres idiomas** están publicados, en
  la fecha más tardía de los tres; la vigente es la última que entró en vigor (RF-003). Se calcula
  al consultar, así que una versión programada a futuro entra sola en vigor cuando llega su fecha.
- **Versión aceptada inmutable**: en cuanto un documento tiene una aceptación (incluso revocada),
  ningún documento de su versión puede cambiar contenido, versión, idioma, tipo, fecha de
  publicación ni exigencia, ni borrarse; para cambiar el texto se crea una versión nueva (RF-005).
- **Aceptar términos** (`UserTerms`) y **conceder o revocar marketing** (`MarketingConsent`): se
  acepta el documento concreto que se mostró (versión + idioma) y solo si es de la versión vigente;
  repetir devuelve la existente; conceder marketing de otra versión sustituye al consentimiento
  activo (revoca el anterior y crea uno nuevo); como máximo un consentimiento activo por usuario; una
  cuenta inactiva no puede aceptar ni conceder, pero sí revocar (RF-006…RF-011, RF-014).
- **Huella del correo**: cada aceptación y consentimiento guarda un HMAC-SHA256 del correo
  normalizado con el secreto `CONSENT_EMAIL_HASH_SECRET`; la calcula siempre el sistema y no cambia
  si el usuario cambia de correo (RF-012). Al borrar la cuenta, las filas se quedan sin usuario pero
  con la huella, y un consentimiento de marketing activo sigue activo (RF-013, S-11).
- **Estado de un usuario**: si tiene los términos aceptados (vale una aceptación en cualquier
  idioma de una versión igual o posterior a la última que exige nueva aceptación; la primera versión
  siempre la exige) y su consentimiento de marketing activo (RF-015, RF-017).
- **Panel de administración**: el staff con permisos sobre «legal documents» crea, edita y publica
  documentos; el grupo **«Soporte técnico»** (creado por la migración `0002`) y los superusuarios
  ven, crean, editan, revocan y borran aceptaciones y consentimientos; nadie más, aunque tenga los
  permisos de modelo (RF-004, RF-018, RF-019).
- **Historial** de las tres tablas con autor, consultable en el panel pero sin poder revertirlo
  (RF-020).

### Límites conocidos
- **Soporte técnico puede fabricar o borrar pruebas** (S-05). El historial deja constancia de quién
  lo hizo, pero no lo impide.
- **Cambiar la exigencia de nueva aceptación de una versión ya creada en varios idiomas no es
  posible desde el panel**: RF-017 rechaza guardar un idioma con un valor distinto del de los
  otros, y se guardan de uno en uno. Hay que decidirla al crear el primer idioma, o borrar los demás
  idiomas (si nadie los aceptó), cambiarla y volver a crearlos.
- **La acción de borrado masivo** rechaza toda la selección (403) si incluye un documento de una
  versión aceptada, también los libres; hay que quitar esos de la selección.
- **Al borrar una cuenta**, el vaciado del usuario en aceptaciones y consentimientos no aparece en
  su historial (lo hace la base de datos con `SET_NULL`); el borrado sí queda en el historial del
  usuario.
- **Un consentimiento de marketing activo de una cuenta borrada** ya solo lo puede revocar soporte,
  y si la persona vuelve a registrarse con el mismo correo puede tener dos activos con la misma
  huella, uno sin usuario (S-11).
- **El secreto de la huella no puede rotar** (S-09): sin definirlo, se usa `DJANGO_SECRET_KEY`, y
  rotar esa clave rompería todas las huellas. Anotado en `HUMAN_TODO.md`.
- La inmutabilidad y la coherencia de la exigencia no se garantizan en cargas masivas ni en SQL
  directo (S-10); las unicidades sí.
- La concurrencia (dos aceptaciones a la vez) está protegida con bloqueos de fila y la unicidad de
  la base de datos, pero ningún test la ejerce con transacciones reales.
- Los textos nuevos están marcados para traducción, pero `makemessages` no se ha ejecutado.
- Durante la feature, `0001_initial` se regeneró varias veces: si aplicaste una versión intermedia
  de la rama, deshaz `consents` (`migrate consents zero`) antes de migrar.

## Cómo probarlo
Requisitos: Docker y la rama `feat/consentimientos`. En el VPS sigue *Actualizar* y *Migraciones*
de la sección *Entorno remoto* del README. En los pasos, `M` abrevia
`docker compose -f docker/docker-compose.yml run --rm backend python manage.py` y `C` abrevia
`M consents`.

1. Levanta la base de datos y Redis y aplica las migraciones. Deberías ver
   `consents.0001_initial... OK` y `consents.0002_support_group... OK`:
   `docker compose -f docker/docker-compose.yml up -d db redis`
   `M migrate`
2. Crea un superusuario para el panel:
   `M createsuperuser --email admin@example.com --name Admin --birthdate 1990-01-01 --country ES`
3. Levanta el backend (`docker compose -f docker/docker-compose.yml up -d backend`) y entra en
   <http://localhost:8000/admin/> con ese usuario. En **Consents → Legal documents** crea seis
   documentos, todos con fecha de publicación de ayer:
   - tipo *Terms of use*, versión `1`, idiomas `es`, `pt-BR` y `en`;
   - tipo *Marketing*, versión `m1`, idiomas `es`, `pt-BR` y `en`.

   Prueba a guardar un contenido con `<p>hola</p>`: verás "Content cannot contain HTML.".
4. Comprueba el documento vigente: `C current --kind terms --locale es` → `version: 1` y el
   contenido. Si quitas la fecha de un idioma, responde "There is no current version…".
5. Crea un usuario de prueba (o usa uno existente) y mira su estado:
   `M shell -c "from datetime import date; from apps.accounts.models import User; User.objects.create_user('ana@example.com', 'una-contraseña-larga', name='Ana García', birthdate=date(1990,5,10), country='ES')"`
   `C status ana@example.com` → `terms: not_accepted` y `marketing: none`.
6. Acepta y concede:
   `C accept-terms ana@example.com --version 1 --locale es` → `accepted: terms 1 (es)`
   `C grant-marketing ana@example.com --version m1 --locale en` → `granted: marketing m1 (en)`
   `C status ana@example.com` → `terms: accepted` y `marketing: marketing m1 (en)`.
   Una versión que no existe (`--version 9`) responde "The document does not exist.".
7. En el panel, abre el documento de términos `1` en inglés: sus campos salen de solo lectura y no
   hay botón de borrar, porque su versión ya tiene una aceptación (aunque sea en español).
8. Revoca el marketing: `C revoke-marketing ana@example.com` → `revoked: marketing m1 (en)`;
   repetirlo responde `revoked: none`.
9. Soporte técnico: crea en el panel un usuario staff, añádelo al grupo **Soporte técnico** y entra
   con él. Verá **Terms acceptances** y **Marketing consents**; selecciona la aceptación de Ana y
   ejecuta la acción **Revoke selected**. En su **History** aparece el cambio con su usuario como
   autor. Un staff fuera del grupo recibe "403 Forbidden" en esas pantallas.
10. Exige una nueva aceptación: crea la versión `2` de términos en los tres idiomas, con
    "Requires reacceptance" marcado y fecha de ayer. Tras aceptar la `1` de nuevo (paso 6),
    `C status ana@example.com` responde `terms: not_accepted` hasta que acepte la `2`.
11. Ejecuta la suite completa (cobertura mínima 80 %):
    `docker compose -f docker/docker-compose.yml run --rm backend pytest -q`

## Marco teórico
### Huella del correo (HMAC)
Una huella es un resumen de longitud fija calculado a partir de un dato. Con un hash simple
(SHA-256 del correo), cualquiera con la base de datos podría probar listas de correos hasta dar con
el que coincide: los correos se adivinan fácilmente. El HMAC mezcla el correo con un **secreto del
servidor**, así que sin ese secreto no se puede ni comprobar ni revertir. Sirve para demostrar, ya
borrada la cuenta, que "quien tenía el correo X aceptó": se calcula la huella de X con el secreto y
se busca. Por eso el secreto no puede cambiar nunca.

### Seudonimización y borrado de la cuenta (`SET_NULL`, `PROTECT`, `CASCADE`)
Al borrar algo referenciado por una FK, la base de datos puede borrar también las filas que lo
apuntan (`CASCADE`), impedir el borrado (`PROTECT`) o vaciar la referencia (`SET_NULL`). Aquí:
borrar la cuenta vacía el usuario de la prueba pero la conserva con su huella (`SET_NULL`), y un
documento aceptado no se puede borrar (`PROTECT`). La prueba sobrevive a la cuenta sin guardar el
correo en claro.

### Versión, entrada en vigor y vigente
Una **versión** es el mismo texto legal en los tres idiomas. **Entra en vigor** cuando están
publicados los tres, en la fecha del último. La **vigente** es la última que entró en vigor. Las
etiquetas de versión son texto libre ("v10" no es mayor que "v9" al comparar texto), así que el
orden lo da la fecha de entrada en vigor, no la etiqueta.

### Exigencia de nueva aceptación
No todo cambio obliga a aceptar de nuevo: corregir una errata no debería. Cada versión indica si
lo exige. Una aceptación vale mientras no entre en vigor una versión posterior que lo exija; la
primera versión siempre lo exige, porque antes no había nada aceptado.

### Por qué la versión aceptada es inmutable
La aceptación apunta a un documento. Si después se pudiera editar su texto, la prueba diría que
alguien aceptó un texto que nunca vio. Bloquear la versión entera (no solo el idioma aceptado)
evita además cambiar su fecha de entrada en vigor, que depende de los tres idiomas.

### Markdown sin HTML (XSS)
El contenido se muestra en la web. Si admitiera HTML, un `<script>` o un `<img onerror=…>` se
ejecutaría en el navegador de quien lo lee (XSS). Markdown permite títulos, listas y enlaces sin
HTML, y el backend rechaza cualquier etiqueta; el frontend debe mostrarlo como Markdown sin
interpretar HTML.

### Restricción única parcial
Una unicidad normal impediría que un usuario tuviera dos consentimientos, incluido el histórico de
los revocados. Una **unicidad parcial** solo se aplica a las filas que cumplen una condición (por
ejemplo, `granted = true`): permite muchos revocados y como mucho un activo, y lo garantiza la base
de datos aunque dos peticiones lleguen a la vez.

### Revocar, deshabilitar y borrar
**Revocar** (o deshabilitar, para soporte) marca la fila con fecha de revocación y la conserva:
deja de contar, pero sigue siendo prueba de lo que pasó. **Borrar** la elimina (queda solo en el
historial). Por eso volver a conceder crea una fila nueva en vez de reactivar la anterior.
