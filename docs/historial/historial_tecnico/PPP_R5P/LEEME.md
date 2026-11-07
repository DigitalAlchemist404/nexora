# Pieza por Pieza — R5-P: contrato semántico v1

Este kit **no ejecuta Qwen** ni cambia resultados anteriores. Genera un contrato semántico y un conjunto sintético nuevo, con 32 ejemplos claros (4 por categoría) y 16 notas ambiguas. Los nombres son neutrales y el manifiesto queda separado del dataset.

```bash
python3 PPP_R5P/r5p.py generate
python3 PPP_R5P/r5p.py validate
```

El contrato se guarda en `~/pieza-lab-r5p-20261105/contract.json` y las respuestas de referencia en `reference/manifest.json`. **No proporcionar el manifiesto al modelo.** No cambiar el contrato después de ver resultados sin versionarlo; toda mejora debe evaluarse en otro conjunto.

Nota: el benchmark es sintético, no prueba generalización a documentos reales. La validación comprueba integridad y ausencia de etiquetas literales, pero no garantiza ausencia de pistas semánticas ni perfección de las etiquetas.
