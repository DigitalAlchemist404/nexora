# R5-P.2 — evaluación bajo contrato semántico

Requiere Python 3.10+, `llama-server` disponible en `127.0.0.1:8080`, y el laboratorio R5-P generado y validado.

Desde la carpeta de descargas:

```bash
unzip PIEZA_POR_PIEZA_R5P2.zip
python3 PPP_R5P2/r5p2.py run --limit 5
python3 PPP_R5P2/r5p2.py run
python3 PPP_R5P2/r5p2.py evaluate
```

El comando `run` **no lee el manifiesto**. Solo lee `contract.json` y `dataset/`, y añade resultados a `r5p2_predictions.jsonl` con sincronización tras cada caso. Si se interrumpe, repite el comando. El comando `evaluate` lee el manifiesto solo después de tener 48 predicciones y crea `r5p2_evaluacion.json` sin sobrescribirlo. No se descargan modelos ni se modifican documentos originales.

Limitaciones: benchmark sintético con plantillas, posible ambigüedad semántica; el prompt incluye ejemplos del contrato predefinido, no respuestas del conjunto de evaluación. El parser tolera un objeto JSON rodeado de texto, pero valida sus claves y categorías. Revisar resultados antes de publicarlos.
