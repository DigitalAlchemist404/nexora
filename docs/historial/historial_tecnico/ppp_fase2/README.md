# Pieza por Pieza — Fase 2, baseline v0.1

Clasificador **sin IA**, conservador y reproducible. Solo usa prefijos de nombres de archivos, no abre contenidos ni el manifiesto. Para nombres `archivo_####` se abstiene. El evaluador se ejecuta **por separado** y sí accede al manifiesto.

## Uso en la GX10 (desde la carpeta descomprimida)

```bash
LAB="$HOME/pieza-lab-20261105"
python3 scripts/baseline.py --dataset "$LAB/dataset" --output "$LAB/baseline_predictions.csv"
python3 scripts/evaluate.py --manifest "$LAB/reference/manifest.json" --predictions "$LAB/baseline_predictions.csv" --output "$LAB/baseline_report.json"
```

Los archivos de salida se crean fuera de `dataset/`; si existen, los scripts se niegan a sobrescribirlos. No se borran ni mueven archivos, no se usa red, Podman, CUDA ni llama-server. La clasificación se ejecuta **en el host**, no dentro del contenedor: las pruebas S1–S3 no se extienden automáticamente a este script. Es un baseline metodológico, no el agente final.

## Interpretación

- `cobertura`: proporción de archivos que el clasificador intenta clasificar.
- `precision_sobre_clasificados`: aciertos entre las predicciones emitidas.
- `exactitud_total_con_abstenciones_como_no_acierto`: aciertos sobre los 1000 archivos.
- `por_dificultad`: desglose según la dificultad **etiquetada por el generador**; no equivale a dificultad humana validada.

**Advertencia:** el dataset v1 contiene fugas artificiales de etiquetas en nombres y contenidos. Una puntuación elevada aquí NO mide generalización real ni demuestra superioridad de un sistema frente a otro. Los tiempos de este baseline no son comparables directamente con la inferencia LLM hasta fijar metodología y condiciones.
