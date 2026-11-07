# Pieza por Pieza — R5-N

Benchmark sintético prospectivo: 32 documentos claros (4 por categoría) y 16 notas deliberadamente ambiguas. El modelo no recibe nombres ni el manifiesto. No modifica experimentos previos.

```bash
python3 PPP_R5N/r5n.py generate
python3 PPP_R5N/r5n.py run --limit 5
python3 PPP_R5N/r5n.py run
python3 PPP_R5N/r5n.py evaluate
```

Requiere llama-server compatible con OpenAI en `127.0.0.1:8080`. El archivo de predicciones JSONL se guarda progresivamente y se reanuda. No se sobrescriben datos ni reportes. **No ajustar el prompt ni el dataset tras ver resultados** si se quiere conservar el carácter prospectivo. Las notas ambiguas tienen como política de referencia abstenerse; no se infiere que cualquier clasificación sea semánticamente incorrecta. Este es un test sintético pequeño, no una prueba de generalización.
