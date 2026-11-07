# Cambios de NEXORA

Lo más nuevo arriba. Las notas de R3/R4 y la investigación previa están en `docs/historial/`.

## R10 — Agrupación más precisa (tras la primera prueba real con visión)

En la prueba real, las 5 fotos de montañas quedaron repartidas en 5 proyectos distintos, IMG_2041 se copió en dos proyectos y 32 de 68 archivos fueron a `Otros`.

1. **Una consulta por archivo** (hasta 300 archivos; por encima, lotes de 10): Qwen ya no se desalinea en listas largas. Acepta como respuesta el número o el nombre del grupo.
2. **Los duplicados exactos van juntos:** se calcula la huella SHA-256 antes de agrupar; las copias idénticas reciben el mismo proyecto y Qwen mira cada foto una sola vez.
3. **Grupos más amplios:** se pide de 3 a 8 grupos que cubran casi todo, guiados por lo que *se ve* y no por nombres como IMG_1234. `Otros` queda solo para lo que no encaja en ninguno.
4. Tests: 42.

## R9 — Carpeta demo ficticia y modo grabación

1. **`demo/crear_carpeta_demo.py`:** crea `~/NEXORA_DEMO/Descargas_demo`, una carpeta "personal" ficticia y desordenada: 71 archivos, 2,9 MB. Tiene fotos dibujadas por código con fecha de cámara, videos, audio, tareas, recetas, duplicados, un archivo sensible y un nombre que intenta darle órdenes a la IA. `--borrar` la elimina; solo borra carpetas con su marca.
2. **Modo grabación** (opción 4 → 5, o `NEXORA_GRABACION=1`): muestra `~` en vez de tu carpeta personal y oculta tu usuario en todo lo que imprime NEXORA.
3. **Recuerda el último modelo y llama-server:** la próxima vez basta con Enter, sin pegar rutas en cámara.
4. **Omitidos con motivo:** "contraseñas_wifi.txt — nombre sensible: no se lee ni se copia".
5. **Nombres sensibles en español:** contraseña, secreto, credencial, pasaporte, cédula, claves.
6. Repositorio ordenado: raíz mínima, historial en `docs/historial/`, guía de grabación en `docs/GRABACION.md`.
7. Tests: 40.

## R8 — Qwen ahora VE

1. **Criterio 7: por lo que muestran las fotos y videos.** Qwen mira cada imagen (y un fotograma de cada video), la describe en pocas palabras y agrupa por proyecto usando nombre + lo que vio. Ideal para `IMG_4032.jpg`.
2. **Criterio 6: por fecha en que se tomó la foto** (EXIF de JPEG, WebP y TIFF, leído sin dependencias). Si no hay EXIF, usa la fecha del archivo y lo indica.
3. **Servidor con visión:** la opción 1 detecta `mmproj-*.gguf` junto al modelo y arranca con `--mmproj`. El estado muestra "Listo (con visión)".
4. **Sin llenar el disco:** las imágenes se reducen a 640 px en memoria (Pillow → ffmpeg → sips, lo que haya). Nada se escribe salvo un temporal de sips en macOS, que se borra al instante.
5. **Seguro:** solo 127.0.0.1; lo que Qwen describe se trata como dato no confiable; si el servidor no tiene visión, NEXORA se detiene y explica cómo activarla.
6. Lo que vio Qwen queda en el manifiesto (`qwen_vio`).
7. Tests: 36 (nuevo `tests/test_r8_vision.py`).

## R7 — Pulido tras la primera prueba con Qwen real

1. **Revisar explica por qué:** "words.json — Qwen dijo 'subtitulos', la extensión sugiere 'datos'". El motivo también queda en el manifiesto (`motivo_revisar`).
2. **Mensajes de ruta claros:** "No existe la carpeta" / "Esa ruta es un archivo, no una carpeta" (antes decía "enlace simbólico" para todo). Acepta rutas pegadas con comillas o espacios.
3. **Pegar la ruta .gguf directo en el menú** de modelos funciona (antes se ignoraba).
4. **Nombres en conflicto más útiles:** `musica__video_playa.m4a` en vez de `musica__assets.m4a` (ignora carpetas genéricas como assets, img, fonts).
5. **`__pycache__` y .pyc se omiten** (eran basura de Python en Revisar).
6. **Proyectos sin archivos** se avisan aparte y no se crean como carpeta.
7. Tests: 30.

## R6 — Cambios sobre R5

1. **Cinco criterios de organización** (opción 9): tipo, tipo + Qwen, **proyecto según nombres (Qwen)**, carpeta de origen, fecha.
2. **Vista previa** del árbol antes de copiar.
3. **SIMULAR:** destinos exactos, duplicados reales y espacio necesario, sin escribir nada. Usa la misma lógica que la copia (comprobado por test).
4. **Chequeo de espacio libre** antes de copiar.
5. **Windows:** archivos abiertos en modo binario (sin esto, las copias fallaban la verificación), unidades C:/D:, `llama-server.exe`, nombres reservados (CON, NUL…), consola sin UTF-8, Thumbs.db/desktop.ini omitidos.
6. **macOS:** `/Volumes`, Homebrew, Python 3.9 de fábrica compatible.
7. Busca modelos también en carpetas de LM Studio.
8. Nombres con saltos de línea ya no pueden alterar las instrucciones enviadas a Qwen.
9. Tests: 27 (nuevo `tests/test_r6_criterios.py`).

## R5 — Cambios sobre R4

1. **Fotos, videos, audio y fuentes ya no van a Revisar.** En R4 la tabla de extensiones existía pero no se usaba: todo binario caía en Revisar (148 de 154 en la prueba real). Ahora: Imagenes, Videos, Audio, Fuentes, Comprimidos, Datos (.npy, .xlsx…), Documentos (.pdf, .docx…).
2. **IA con confianza "media" que coincide con la extensión se acepta.** Antes solo "alta" pasaba; LEEME.txt y words.json terminaban en Revisar.
3. **Duplicados exactos** (mismo SHA-256, misma categoría) se copian una vez; quedan listados en `MANIFIESTO_PRIVADO.json` → `duplicados`.
4. **Conflictos de nombre usan la carpeta de origen:** `LEEME__homenaje.txt` en vez de `LEEME__1.txt`.
5. **Ctrl+C** sale limpio, sin traceback, y cierra el servidor propio.
6. **Configuración guardada** en `~/.config/nexora/config.json` (capas GPU ya no vuelve a 0).
7. **"Pegar ruta GGUF"** pide la ruta directamente.
8. Resumen final y categorías legibles; tamaño en MiB.
9. README actualizado (ya no contradice la opción 9). Tests nuevos: `tests/test_r5_correcciones.py`.
