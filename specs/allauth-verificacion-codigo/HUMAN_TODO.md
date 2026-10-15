# HUMAN_TODO — allauth-verificacion-codigo

Acciones que **requieren intervención humana** para completar la feature `allauth-verificacion-codigo`
(credenciales, instalaciones locales, binarios, decisiones de infraestructura). Marca `[x]`
cuando completes cada una y muévela a *Hecho* con la fecha.

## Pendiente

- [ ] **Decidir los límites de peticiones (rate limiting) de allauth en `auth-headless`.**
  Hallazgo C-15 del spike `allauth-verificacion-codigo`: `ACCOUNT_RATE_LIMITS = {}` en
  `backend/config/settings.py` **no** desactiva los límites de allauth (solo `False` lo hace).
  Siguen activos, entre otros, 5 logins fallidos cada 5 min por correo y 20 registros por minuto
  e IP. Esto contradice S-09 de `specs/auth-headless/spec.md`, y ejecutar la suite más de 5 veces
  en 5 minutos hace fallar sus tests de login (`too_many_login_attempts`). Elige una opción:
  - **Mantener los límites** (recomendable para producción): corregir S-09 y el resumen de
    `auth-headless` para que digan la verdad, y aislar los tests de login de los contadores.
  - **Desactivarlos** como dice S-09: poner `ACCOUNT_RATE_LIMITS = False`.

  Siguiente paso, en ambos casos: `sdd-cambio` sobre `auth-headless` en una rama `fix/`.

## Hecho

- [x] **Acceso de escritura a GitHub para las sesiones web** (2026-09-28). GitHub reconectado;
  la rama `spike/allauth-verificacion-codigo` se subió correctamente.
