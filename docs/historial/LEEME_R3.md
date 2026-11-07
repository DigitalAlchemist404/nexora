# NEXORA BETA R3 — Integración local

Nueva opción **8**: ejecuta el clasificador Qwen directamente desde el menú, usando la muestra local ya aprobada. Solicita explícitamente confirmación. Usa `chat_template_kwargs.enable_thinking=false`, `max_tokens=128`, y exclusivamente `127.0.0.1:8080`. Conserva respaldo de resultados antes de sobrescribirlos.

## Prueba rápida

```bash
cd nexora-repositorio
python3 -m unittest discover -s tests -v
python3 iniciar.py
```

**Antes de iniciar el servidor**, fijar GPU=99 y reasoning off=True en configuración avanzada (si tu compilación lo soporta); el menú no reinicia automáticamente un servidor ya activo. La opción 8 necesita servidor listo, aprobación previa y el mapa privado en `~/NEXORA_QWEN_RESULTADOS/`.

**Secuencia:** 4 (configurar) → 1 (iniciar servidor) → 2 (confirmar Listo) → 8 (clasificar) → 7 (auditoría y copias). La opción 7 conserva sus controles de seguridad y únicamente copia archivos en que reglas y Qwen coinciden con confianza alta.

**Limitaciones:** no se ha validado en el GX10 esta versión R3; no mide exactitud sin etiquetas humanas, no organiza originales ni implementa undo de movimientos reales. Al salir con 0, el servidor administrado por el menú se detiene (comportamiento existente). No compartas `MAPA_PRIVADO_NO_COMPARTIR.json`.
