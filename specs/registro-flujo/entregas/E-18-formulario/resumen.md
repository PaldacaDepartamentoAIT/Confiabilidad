# Entrega E-18 · Pantalla del formulario: campos y comprobaciones

Rama: `feat/registro-flujo-formulario` · PR: pendiente ·
Líneas de código y tests: 371 (límite: 400).

## Qué se hizo
- **Pantalla del formulario de registro** (`frontend/src/registration/RegisterPage.tsx`), todavía
  sin ruta y sin envío al servidor (el envío llega en E-19):
  - pide al servidor las opciones del formulario y, mientras tanto, no muestra campos;
  - campos de nombre completo, fecha de nacimiento (selector de fecha), correo y país, todos
    obligatorios, y las casillas de términos (obligatoria) y de marketing (opcional, sin marcar);
  - los países se muestran por su nombre en el idioma activo y ordenados (`Intl.DisplayNames`);
  - los términos y el texto del marketing se leen en desplegables. La casilla de marketing solo
    aparece si hay un documento de marketing vigente;
  - sin términos vigentes, la pantalla dice que ahora no es posible registrarse y no muestra el
    formulario. Si las opciones no se pueden cargar, avisa del fallo de conexión;
  - al enviar con errores, pinta cada error bajo su campo, desplaza la página hasta el primero, le
    lleva el foco y no llama al servidor.
- **Markdown de los documentos** con `react-markdown` (dependencia nueva aprobada el 2026-11-03,
  `^10.1.0`): el texto de los términos y del marketing se escribe en Markdown sin HTML (S-14 de
  `consentimientos`). Se muestran negritas, párrafos y enlaces, y el HTML nunca se interpreta.

## Tareas
El detalle de la tarea, con su «Hecho cuando», está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commits |
|---|---|---|
| T-043 | Pantalla del formulario: campos y comprobaciones | `43f3022`, `7be26ba` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias (incluye `react-markdown`):
```bash
pnpm install
```
Ejecuta los tests de la pantalla:
```bash
pnpm --filter frontend exec vitest run src/registration/RegisterPage
```
Deberías ver 9 tests en verde: carga de opciones y campos, países en portugués, acceso a los
textos, Markdown sin HTML, sin marketing, sin términos vigentes, fallo de conexión, envío vacío y
correo mal escrito. Ejecuta la suite completa del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 300 tests en verde. La pantalla todavía no tiene ruta: se podrá abrir en
http://localhost:5173/register a partir de E-15.

## Marco teórico
- **Por qué renderizar Markdown con una librería.** El texto legal lo escribe una persona en
  Markdown (`**negrita**`, párrafos separados por una línea en blanco, enlaces). Mostrarlo tal cual
  dejaría los asteriscos a la vista y todo en un párrafo. Una librería probada lo convierte en
  elementos de la página y, sin configuración extra, descarta cualquier HTML que se cuele en el
  texto: así nadie puede inyectar un `<script>` a través de un documento.
- **Nombres de países sin traducirlos a mano.** El servidor envía códigos ISO (`ES`, `BR`). El
  navegador ya sabe nombrarlos en cada idioma con `Intl.DisplayNames`, así que no hace falta una
  lista de traducciones: `ES` se ve «España» en español y «Espanha» en portugués.
