# Pieza por Pieza — R5-L

## 1. Qué pasó con los PNG originales

Los PNG de Fase 1 **son imágenes PNG válidas** (16x16 RGB, píxeles aleatorios, compresión zlib y CRC). **No son fotografías reconocibles**: el generador no dibuja objetos ni escenas. La categoría está en el manifiesto, no en los píxeles. R5-J pasó el marcador «contenido binario no interpretado» en lugar de píxeles a Qwen. Por tanto, no podía reconocer visualmente su contenido.

## 2. Comandos (Python 3, solo biblioteca estándar)

```bash
python3 PPP_R5L/r5l.py replay
python3 PPP_R5L/r5l.py generate
```

`replay` simula retrospectivamente abstenerse en PNG sin visión; no modifica nada. `generate` crea una carpeta **nueva** `~/pieza-lab-r5l-20261106/` con 64 textos sin etiquetas explícitas y 8 PNG abstractos. Si existe, se niega a sobrescribir.

## 3. Alcance y siguientes pasos

Este es un **nuevo conjunto pequeño de diagnóstico**, no un benchmark realista de documentos. Los textos tienen frases escritas específicamente para cada categoría, así que siguen siendo relativamente fáciles. Los PNG nuevos siguen siendo patrones abstractos sin contenido semántico: deben usarse para comprobar abstención segura, no reconocimiento visual. Para medir imágenes reales, hará falta otro dataset con escenas/objetos y un pipeline visual validado.

**No pasar el manifiesto al modelo**. Conservar la referencia fuera del directorio de entrada. Aún no se llama a Qwen; el siguiente paso es un evaluador ciego para el nuevo conjunto, antes de abrir la referencia.

No se cambia ni se descarga ningún modelo, no se alteran datos anteriores y no se hacen operaciones sobre archivos del usuario.
