# HUMAN_TODO · componentes-base-accesibles

## Pendiente

- [ ] **Quitar la atribución del commit de la spec.** El commit
  `docs: especifica la feature componentes-base-accesibles` de la rama
  `claude/wizardly-babbage-c6di7v` lleva las líneas `Co-Authored-By` y `Claude-Session`, que
  `AGENTS.md` prohíbe (P-10). El entorno remoto no puede reescribir la rama ya subida. Hay dos
  formas de quitarlas: fusionar el PR con «Squash and merge» y borrar esas líneas del mensaje, o
  reescribir el commit desde tu máquina.

  Para reescribirlo, mira primero en qué posición está ese commit:
  ```bash
  git log --oneline origin/main..origin/claude/wizardly-babbage-c6di7v
  ```
  Deberías ver los commits de la rama, del más reciente al más antiguo. Si el de la spec es el
  único, ejecuta:
  ```bash
  git fetch origin claude/wizardly-babbage-c6di7v
  ```
  ```bash
  git checkout claude/wizardly-babbage-c6di7v
  ```
  ```bash
  git reset --hard origin/claude/wizardly-babbage-c6di7v
  ```
  ```bash
  git commit --amend -m "docs: especifica la feature componentes-base-accesibles"
  ```
  ```bash
  git push --force-with-lease origin claude/wizardly-babbage-c6di7v
  ```
  Si hay más commits encima, usa la opción de «Squash and merge» en lugar de reescribir la rama.

## Hecho
