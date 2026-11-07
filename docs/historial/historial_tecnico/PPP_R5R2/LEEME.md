# Pieza por Pieza — R5-R.2: batería de pruebas de seguridad

Esta entrega reutiliza **sin cambios** el ejecutor `r5r.py` de R5-R y añade `test_r5r2.py`. No ejecuta Qwen, no lee archivos personales ni modifica el laboratorio original. Cada prueba crea un directorio temporal nuevo y lo elimina al finalizar.

## Ejecución

Desde la carpeta donde descomprimiste el ZIP:

```bash
python3 PPP_R5R2/test_r5r2.py
```

El resultado esperado es `Ran 8 tests ... OK`. Se prueban: ausencia de autorización, digest incorrecto, alteración de hash, colisión de destino, enlace simbólico de destino, manipulación de ruta en el plan, repetición de ejecución/reversión y reanudación tras un movimiento parcial simulado.

## Límites que no debemos ocultar en el video

- Estas pruebas **no demuestran** seguridad frente a un atacante concurrente. El ejecutor usa comprobaciones de ruta y después `os.rename`; existen ventanas TOCTOU.
- El simulacro de interrupción representa un movimiento completado sin registro; **no prueba** caída de energía, fallo de disco, transacciones atómicas ni recuperación de cualquier estado intermedio.
- El laboratorio no es un sandbox del sistema operativo y el marcador `.r5r_lab` no es una frontera de seguridad contra usuarios hostiles.
- El script usa rutas de un directorio temporal y nunca debe ejecutarse como administrador/root. No copiar el laboratorio sobre carpetas reales.
- El plan utiliza etiquetas sintéticas conocidas; no evalúa clasificación de Qwen.
- El escáner de privacidad y la revisión humana siguen siendo necesarios antes de publicar código, logs o grabaciones.

## Próximo hito

Congelar la evidencia de las pruebas, generar gráficos y capturas con rutas relativas, y preparar el guion de 12–18 minutos y los cinco Shorts. Si queremos afirmar seguridad ante adversarios, hará falta rediseñar el ejecutor con primitivas de sistema de archivos más fuertes y nuevas pruebas.
