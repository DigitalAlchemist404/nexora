# Pieza por Pieza — R5-K

Auditoría **offline**, sin dependencias externas y sin invocar Qwen.

```bash
python3 r5k_auditoria.py
```

Requiere el laboratorio original en `~/pieza-lab-20261105` con `reference/manifest.json`, `baseline_predictions.csv`, `r5_piloto.json`, `r5j_predictions.jsonl` y `dataset/`.

Crea una sola vez `~/pieza-lab-20261105/r5k_auditoria/` con `resumen.json`, `casos.csv`, `errores_y_abstenciones.csv`. No sobrescribe el destino. Para una nueva corrida, pasar `--out` a una carpeta nueva.

**Advertencia metodológica**: el generador de fase 1 incluye etiquetas de categoría explícitas en TXT, MD, CSV, JSON y PDF, incluso en casos marcados ambiguos. Las imágenes PNG son píxeles aleatorios. Los resultados R5-J no validan generalización a documentos reales. R5-K sirve para diagnóstico y preparación de un dataset ciego posterior.
