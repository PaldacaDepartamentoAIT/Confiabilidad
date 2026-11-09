# Entrega E-02 · Módulo de tema y textos

Rama: `feat/sistema-de-diseno-modulo-tema` · PR: [PaldacaDepartamentoAIT/Confiabilidad#67](https://github.com/PaldacaDepartamentoAIT/Confiabilidad/pull/67) ·
Líneas de código y tests: 252 (límite: 400).

## Qué se hizo
- Hay un módulo que decide el tema de la aplicación: si el usuario eligió uno y quedó guardado, lo
  aplica; si no, sigue al sistema operativo. Un valor guardado que no sea «light» ni «dark» se
  ignora y se borra. Si el navegador bloquea el almacenamiento, la aplicación funciona igual, sin
  recordar la elección.
- Alternar el tema lo cambia, lo guarda y marca la página durante 0,4 s para que la transición de
  colores sea suave (el estilo de esa transición llega con el botón, en E-02b).
- Los textos del botón de tema existen en español, portugués de Brasil e inglés.
- Esta entrega no muestra nada nuevo en la pantalla: el botón y su uso al arrancar son E-02b. La
  entrega original medía 515 líneas y, por el límite de 400, se dividió por decisión del usuario.

## Tareas
El detalle de cada tarea está en [`tasks.md`](../../tasks.md).

| Tarea | Título | Commit |
|---|---|---|
| T-002 | Módulo de tema | `cd76fbc` |
| T-003 | Textos del tema en tres idiomas | `029c22c` |

## Cómo ejecutarlo y probarlo
Desde la raíz del repositorio, instala las dependencias:
```bash
pnpm install
```

Ejecuta los tests del frontend:
```bash
pnpm --filter frontend test
```
Deberías ver 31 archivos de test en verde, entre ellos `src/theme/theme.test.ts` (17 tests: tema
inicial, valor guardado inválido y alternar con su plazo de 0,4 s) y los de las traducciones.

## Marco teórico
- **Almacenamiento inyectable:** el módulo recibe dónde guardar el tema en lugar de usar siempre el
  del navegador. Así los tests lo prueban con uno falso, incluido uno que falla, sin tocar el real.
- **Tema fijado frente a tema del sistema:** sin elección guardada no se escribe nada en la página y
  el CSS sigue al sistema operativo; solo cuando el usuario pulsa el botón se fija `data-theme` en
  `<html>`.
