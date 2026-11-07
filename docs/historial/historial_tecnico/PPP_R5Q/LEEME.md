# Pieza por Pieza — R5-Q

Simulación de decisiones sobre las 48 predicciones existentes de R5-P.2. **No mueve archivos, no llama al modelo y no consulta el manifiesto de referencia.**

## Ejecutar

Desde `~/Downloads/lab`:

```bash
unzip PIEZA_POR_PIEZA_R5Q.zip
python3 PPP_R5Q/r5q.py
```

Ruta por defecto: `~/pieza-lab-r5p-20261105`. Si el laboratorio está en otra carpeta, usar `--root RUTA`. Si ya existe el directorio de resultados, usar `--output RUTA_NUEVA` (no se sobrescribe).

## Interpretación

- `PROPUESTA_PENDIENTE_APROBACION`: salida estructuralmente válida y categoría reconocida. **No significa que la categoría sea correcta.**
- `ABSTENCION_SIN_ACCION`: Qwen se abstuvo.
- `BLOQUEADO_*`: datos inválidos o categoría fuera del contrato.

Todos los casos quedan sin aprobación y sin movimiento. Este simulador valida hashes y nombres simples, pero **no es todavía un ejecutor seguro** ni una prueba de seguridad contra TOCTOU, symlinks complejos o ataques al filesystem. Antes de ejecutar movimientos reales hacen falta aprobación humana vinculada a un plan inmutable, controles del filesystem y pruebas de aislamiento.

No publicar `propuestas.csv` sin revisar los nombres de archivos.
