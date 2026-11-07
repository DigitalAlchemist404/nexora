# Bitácora de experimentos — versión para publicación

| Fase | Resultado observado | Limitación |
|---|---|---|
| F1 | 1,000 documentos sintéticos | Plantillas, distribución artificial |
| F2 | Reglas: 910 aciertos, 90 abstenciones | Nombres artificiales facilitan la tarea |
| R5-J | Híbrido: 978 aciertos, 13 errores, 9 abstenciones | PNG sin capacidad visual |
| R5-K | Los 13 errores se concentraron en PNG | PNG son ruido sintético 16×16, no fotografías |
| R5-L | 976 aciertos, 0 errores, 24 abstenciones | Política decidida después de observar errores |
| R5-L.2 | 63/64 textos correctos, 8 PNG abstenciones | Dataset nuevo, sintético y pequeño |
| R5-N | 43/48 cumplimiento; 29/32 claros; 14/16 ambiguos abstenciones | Semántica de misceláneos no fijada |
| R5-O | Auditoría de cinco discrepancias | Discrepancia de política no equivale a error semántico |
| R5-P | 48 TXT nuevos; estructura e hashes validados | Etiquetas potencialmente debatibles |
| R5-P.2 | 32/32 claros correctos; 11/16 ambiguos abstenciones; 43/48 política; 0.794 s media | No generalizar a documentos reales |
| R5-Q | 48 predicciones verificadas; 37 propuestas; 11 abstenciones; 0 movimientos | Simulación, no ejecución real |

No cambiar las métricas históricas ni presentar experimentos post hoc como prospectivos. Mantener evidencias y hashes privados hasta una revisión de publicación.
