# HUMAN_TODO · componentes-base-accesibles

## Pendiente

- [ ] **Borrar la rama remota `claude/wizardly-babbage-c6di7v` sin fusionarla.** Contiene un commit
  con líneas de atribución que `AGENTS.md` prohíbe (P-10). Sus documentos (spec, plan y tareas) ya
  están, en commits limpios, en `feat/componentes-base-accesibles-traduccion`. El entorno remoto no
  puede borrar ramas en GitHub. Desde tu máquina:
  ```bash
  git push origin --delete claude/wizardly-babbage-c6di7v
  ```

- [ ] **Decidir qué hacer con la rama `fix/componentes-base-accesibles-idioma-inicial` (T-041).**
  Fija `<html lang>` antes de montar la página, pero no cambió lo que se oye con NVDA, así que no
  se fusionó. Si no se retoma (por ejemplo, en una investigación del modo exploración), bórrala
  desde tu máquina:
  ```bash
  git push origin --delete fix/componentes-base-accesibles-idioma-inicial
  ```

## Hecho

- [x] **Completar los checklists de teclado y de lector de pantalla (CF-3, CF-5).** Recorridos con
  NVDA + Chrome el 2026-10-27 y el 2026-10-28. Todo pasa salvo la voz del idioma activo en los
  nombres de los campos, aceptada como riesgo residual (ver «Límites conocidos» en
  [`resumen.md`](resumen.md)).

- [x] **Comprobar que el contenedor `frontend` arranca con las dependencias nuevas (E-01, E-02,
  E-04).** Comprobado por el usuario en local el 2026-10-28.
