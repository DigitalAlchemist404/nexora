# Pieza por Pieza — Fase 1 (paquete inicial)

Generador **sin dependencias externas** de 1,000 archivos sintéticos reproducibles para Linux ARM64 o cualquier Python 3.10+.

## Uso (no requiere llama-server)

```bash
python3 scripts/dataset.py generate --root "$HOME/pieza-lab-20261105" --seed 20261105
python3 scripts/dataset.py validate --root "$HOME/pieza-lab-20261105"
bash scripts/podman_probe.sh
```

**No usar un directorio que ya exista**: el generador rechaza sobrescrituras. No hay comandos de limpieza automática.

El clasificador solamente debe recibir la carpeta `dataset/`; **nunca** montar ni entregar `reference/manifest.json` al clasificador. El manifiesto contiene la verdad de referencia.

## Distribución

- Universidad 180
- Finanzas ficticias 120
- Fotografías 160
- Programación 150
- Trabajo 120
- Ciencia 100
- Entretenimiento 90
- Misceláneos 80

Formatos: TXT, Markdown, CSV, JSON, PDF y PNG. Los PDF son documentos mínimos válidos y los PNG son imágenes sintéticas de 16×16. **No se representan fotografías reales**; la categoría `fotografias` es una etiqueta sintética. No se usan datos personales.

## Limitaciones y seguridad

- El validador revisa estructura básica de PDF/PNG y hashes; **no sustituye** a validadores especializados de terceros ni a pruebas con visores.
- El dataset actual contiene textos simples con pistas explícitas de categoría. No es todavía una prueba robusta de clasificación semántica, documentos difíciles ni comprensión de imágenes.
- Los nombres ambiguos prueban el uso del contenido para TXT/MD/CSV/JSON/PDF; PNG contiene píxeles aleatorios y no una escena semántica.
- No hay ejecutor de movimientos ni acceso a archivos reales.
- Podman **no está certificado**: el script `podman_probe.sh` solo consulta el estado y propone flags para revisión. No inicia contenedores ni instala imágenes.
- No se cambia la configuración de `llama-server`, ni se usa el puerto 8080.
- El directorio `reference/` es privado al evaluador y no debe publicarse junto a entradas de evaluación antes del benchmark.

## Próximas tareas

1. Validación independiente con visores/herramientas externas y pruebas de aislamiento rootless.
2. Diseñar casos difíciles y formatos con contenido visual semántico (sin romper la reproducibilidad).
3. Implementar baseline por reglas y evaluación sin fuga del manifiesto.
4. Revisar aprobación por lotes y plan inmutable antes de cualquier movimiento.
