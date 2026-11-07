# NEXORA — integración de auditoría de Qwen y copias

Este paquete se deriva del repositorio BETA compartido y añade **opción 7** al menú existente.

## Ejecutar (sin reemplazar tu repositorio anterior)

```bash
cd "$HOME/Downloads/lab"
unzip NEXORA_BETA_INTEGRADA_R2.zip
cd NEXORA_BETA_INTEGRADA_R2/nexora-repositorio
python3 iniciar.py
```

La opción 7 reutiliza los archivos locales `~/NEXORA_QWEN_RESULTADOS/RESULTADOS_QWEN.csv`, `APROBAR_MUESTRA.csv` y `MAPA_PRIVADO_NO_COMPARTIR.json`. El mapa privado **no está incluido** en este paquete y **no debe compartirse**. La opción 7.1 audita sin leer originales. La opción 7.2, previa confirmación explícita, lee solo archivos aprobados y crea copias verificadas, además de un ensayo de restauración de copias. No mueve originales ni constituye un rollback de movimientos reales.

`ETIQUETAS_PARA_REVISION.csv` contiene las 30 predicciones sin rutas privadas. Se deben completar las etiquetas humanas tras revisar contenido autorizado, **sin asumir que las reglas son la verdad**. Hay 14 desacuerdos entre reglas y Qwen (11 documentos->código, 2 documentos->datos, 1 documento->revisar).

**Pendiente:** conectar inferencia Qwen directa al menú (la opción 7 reutiliza resultados ya existentes), validar etiquetas humanas y añadir movimiento real con reversión antes de afirmar que el producto está completo. El servidor iniciado desde el menú todavía se detiene al salir, como en BETA.
