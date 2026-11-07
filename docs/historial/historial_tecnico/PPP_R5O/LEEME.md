# R5-O — Auditoría offline de discrepancias

Ejecutar desde cualquier carpeta:

```bash
python3 PPP_R5O/r5o_auditoria.py
```

Por defecto busca el laboratorio en `~/pieza-lab-r5n-20261106`. Si tiene otro nombre, usar `--root RUTA`.

Si detecta varios archivos de predicciones, elegir el correcto con `--predicciones RUTA`. No modifica los datos. Para ver el contenido de los cinco documentos, añadir `--mostrar-contenido`; revisar los textos antes de compartirlos.

El auditor requiere que el manifiesto identifique `tipo` (`claro`/`ambiguo`), categoría esperada y nombre. Si la estructura difiere, muestra los campos y se detiene sin inventar resultados.
