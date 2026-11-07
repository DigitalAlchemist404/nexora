# Política de privacidad y publicación

## No publicar
- Rutas absolutas de carpetas personales, nombres de usuario, nombres de equipo, direcciones IP privadas si revelan infraestructura, archivos personales.
- Claves, tokens, `.env`, sesiones, cookies, historiales, SSH keys, identificadores de cuentas.
- Manifiestos privados de evaluación, datos originales sin revisión, modelos grandes.
- Capturas de terminal con prompt real o rutas del HOME.

## Flujo recomendado
1. Trabajar con el repositorio en un directorio separado.
2. Ejecutar `python3 scripts/privacy_scan.py .`.
3. Ejecutar `git status --short` y `git diff --cached --name-only` antes de cada commit.
4. Revisar manualmente todos los archivos incluidos, especialmente binarios y multimedia.
5. Publicar inicialmente como repositorio **privado** y revisar antes de hacerlo público.
6. Nunca asumir que `.gitignore` borra secretos ya versionados. Si se subió una credencial, revocarla y rotarla.

El escáner detecta patrones simples en archivos de texto. No inspecciona imágenes, video, audio ni todos los secretos posibles. Un resultado limpio **no certifica privacidad**.
