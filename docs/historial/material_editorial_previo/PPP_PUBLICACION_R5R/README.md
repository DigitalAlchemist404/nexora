# Pieza por Pieza — Agente local para organizar archivos

Investigación reproducible con datos **sintéticos**, modelo local y autorización humana.

## Estado
- Dataset original: 1,000 archivos sintéticos.
- Reglas: 910 correctos, 0 incorrectos, 90 abstenciones.
- Híbrido inicial: 978 correctos, 13 incorrectos, 9 abstenciones.
- Política PNG post hoc: 976 correctos, 0 incorrectos, 24 abstenciones. **No es un benchmark prospectivo.**
- R5-P.2: 32/32 claros correctos; 11/16 ambiguos con abstención; cumplimiento 43/48.
- R5-Q: 37 propuestas pendientes, 11 abstenciones, 0 movimientos.

**Estos resultados proceden de ejecuciones reportadas por el operador.** El repositorio inicial contiene documentación y utilidades de publicación; no contiene los datasets históricos ni afirma reproducir sus cifras sin esos artefactos.

## Seguridad
Este repositorio no mueve archivos reales. Las demostraciones deben realizarse en una copia sintética desechable. No subir modelos GGUF, manifiestos privados, rutas de la máquina, tokens, claves ni grabaciones sin revisión.

## Primeros pasos
```bash
python3 scripts/privacy_scan.py .
python3 scripts/make_demo.py --out demo_publica
python3 scripts/privacy_scan.py demo_publica
```

La carpeta `demo_publica/` se ignora por Git. Antes de publicar, revisar manualmente **todo** el material, incluidas imágenes, video, audio y metadatos; el escáner no garantiza ausencia de datos sensibles.

## Próximos hitos
1. R5-R: ejecutor reversible de laboratorio, con aprobación explícita y pruebas adversariales (pendiente).
2. R5-S: gráficos y captura pública.
3. R5-T: guion de 12–18 minutos y cinco Shorts.

Consulta `docs/PLAN_VIDEO.md`, `docs/SEGURIDAD_PUBLICACION.md`, `docs/BITACORA.md`.
