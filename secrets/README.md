# Secretos de producción (SOPS + age)

En este directorio van **solo** los secretos de producción **cifrados** con SOPS + age
(archivos `*.enc.yaml` / `*.enc.env`). Nunca se guardan valores en claro.

## Primer uso
1. Genera tu par de claves age (guárdala fuera del repo):
   ```bash
   age-keygen -o age-key.txt
   ```
2. Copia la clave pública (`age1...`) al `.sops.yaml` de la raíz.
3. Crea/edita un secreto cifrado:
   ```bash
   sops secrets/prod.enc.yaml
   ```

## En despliegue
Se descifra con la clave privada (variable `SOPS_AGE_KEY` o archivo de clave):
```bash
sops --decrypt secrets/prod.enc.yaml > /run/secrets/prod.env
```
Los secretos de producción no se descifran fuera del proceso de despliegue.
