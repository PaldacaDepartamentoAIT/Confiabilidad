# HUMAN_TODO · componentes-base-accesibles

## Pendiente

- [ ] **Borrar la rama remota `claude/wizardly-babbage-c6di7v` sin fusionarla.** Contiene un commit
  con líneas de atribución que `AGENTS.md` prohíbe (P-10). Sus documentos (spec, plan y tareas) ya
  están, en commits limpios, en `feat/componentes-base-accesibles-traduccion`. El entorno remoto no
  puede borrar ramas en GitHub. Desde tu máquina:
  ```bash
  git push origin --delete claude/wizardly-babbage-c6di7v
  ```

- [ ] **Comprobar que el contenedor `frontend` arranca con las dependencias nuevas (E-01, E-02, E-04).** En el
  entorno remoto, el contenedor no tiene salida a internet: Corepack no puede descargar pnpm
  (`getaddrinfo EAI_AGAIN registry.npmjs.org`) y falla antes de llegar a `pnpm install`, también
  sin los cambios de esta rama. Desde la raíz del repositorio, en tu máquina:
  ```bash
  docker compose -f docker/docker-compose.yml up frontend
  ```
  Deberías ver que Vite queda escuchando en el puerto 5173 y la página en http://localhost:5173 en
  el idioma de tu navegador.

- [ ] **Completar los checklists de teclado y de lector de pantalla (CF-3, CF-5).** La prueba con un
  lector real no se puede automatizar (S-08). Sigue «Checklist de teclado» y «Checklist de lector
  de pantalla» en [`resumen.md`](resumen.md), con NVDA en Windows o VoiceOver en macOS, marca allí
  cada punto y después esta acción. Para arrancar la página, desde la raíz del repositorio:
  ```bash
  pnpm --filter frontend dev
  ```
  Deberías ver la página de muestra en http://localhost:5173.

## Hecho
