# Iconos de Tauri

Este directorio debe contener los iconos de la app (`32x32.png`, `128x128.png`,
`128x128@2x.png`, `icon.icns`, `icon.ico`). No se versionan de ejemplo porque son
binarios; genéralos una vez con:

```bash
pnpm --filter desktop tauri icon ruta/a/tu-icono.png
```
