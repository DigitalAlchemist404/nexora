# Pieza por Pieza — R5-R

**Laboratorio sintético de ejecución autorizada y reversible.** No usa Qwen ni sus predicciones: el plan se deriva de una referencia ficticia para demostrar el ejecutor, no para medir precisión de clasificación.

Desde la carpeta donde descomprimiste el ZIP:

```bash
python3 PPP_R5R/r5r.py prepare --root ./r5r_demo_lab
python3 PPP_R5R/r5r.py plan --root ./r5r_demo_lab
python3 PPP_R5R/r5r.py verify --root ./r5r_demo_lab
```

Copiá el digest completo impreso por `plan` y autorizá explícitamente:

```bash
python3 PPP_R5R/r5r.py approve --root ./r5r_demo_lab --digest 'PEGAR_DIGEST' --confirm 'AUTORIZO DEMO R5R'
python3 PPP_R5R/r5r.py execute --root ./r5r_demo_lab
python3 PPP_R5R/r5r.py verify --root ./r5r_demo_lab
python3 PPP_R5R/r5r.py rollback --root ./r5r_demo_lab
python3 PPP_R5R/r5r.py verify --root ./r5r_demo_lab
```

El laboratorio debe crearse en un directorio **nuevo y vacío**. `prepare` se niega a sobrescribir rutas existentes. No pases rutas de documentos personales. No uses `sudo`.

## Límites de seguridad

- Usa únicamente TXT sintéticos; no toca laboratorios históricos.
- Rechaza rutas con `..`, enlaces simbólicos en rutas examinadas, archivos no regulares, hardlinks de origen, colisiones y cambios de hash.
- El plan requiere autorización explícita ligada a su SHA-256; cada movimiento y reversión se registra en SQLite.
- `execute` se puede reintentar tras interrupción, aunque no hay garantía transaccional frente a corte eléctrico.
- **No es un sandbox adversarial ni un ejecutor listo para producción**: las comprobaciones de rutas tienen posibles carreras TOCTOU si otro proceso modifica el árbol simultáneamente. Ejecutar en directorio privado, sin procesos no confiables. No demuestra ausencia de accesos externos en todos los escenarios.
- El plan incluye las etiquetas sintéticas correctas; no es una prueba de exactitud de Qwen.
- Para GitHub: publicar solo código, documentación y datos sintéticos revisados; nunca el historial de tu carpeta personal, capturas sin inspección ni credenciales.
