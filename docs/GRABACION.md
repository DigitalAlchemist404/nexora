# Grabar NEXORA sin mostrar datos personales

Objetivo: tomar todas las capturas del video con la carpeta **ficticia**, sin que aparezcan tu usuario, tus rutas ni tus archivos reales.

## 1. Preparar (fuera de cámara, una sola vez)

1. Crea la carpeta ficticia:
   ```bash
   python3 demo/crear_carpeta_demo.py
   ```
2. Abre NEXORA, ve a la **opción 4 → 5** y activa el **modo grabación**. Queda guardado.
3. **Opción 1:** inicia el modelo **con visión** y espera a que la opción 2 diga `Listo (con visión)`. Haz esto antes de grabar: al pegar la ruta del modelo, la terminal la muestra tal cual. Desde la segunda vez, NEXORA recuerda el modelo y basta con Enter.
4. Terminal limpia, solo para esta ventana (al cerrarla vuelve tu prompt normal):
   - fish: `function fish_prompt; echo '$ '; end`
   - bash/zsh: `PS1='$ '`
5. Letra grande (unos 22 pt), tema oscuro y ventana vertical si es para Shorts. Revisa que la barra de título no muestre `usuario@equipo`; si la muestra, recorta o usa pantalla completa.
6. Trabaja desde la carpeta de la demo, así `tree` muestra rutas cortas. **No uses `tree ~/NEXORA_DEMO/...`: la primera línea mostraría `/home/tu_usuario/...`.**
   ```bash
   cd ~/NEXORA_DEMO
   ```

## 2. Qué capturar

| Archivo | Qué hacer | Qué se ve |
|---|---|---|
| `antes.png` | `tree -L 1 Descargas_demo` | El desorden: IMG_xxxx, "Nueva carpeta (2)", copias… |
| `menu.png` | Abrir NEXORA | Menú principal y `[modo grabación…]` |
| `servidor_vision.png` | Opción 2 | `Estado: Listo (con visión)` |
| `criterios.png` | Opción 9 → 1 → `~/NEXORA_DEMO/Descargas_demo` | Los 7 criterios |
| `omitidos.png` | Cualquier criterio | `omitido contraseñas_wifi.txt — nombre sensible` |
| `nombres_fallan.png` | Criterio 3 | Con nombres `IMG_xxxx`, Qwen no sabe dónde va cada foto (muchas en `Otros/`) |
| `vision_progreso.png` | Criterio 7 | `vistas N/N` y las líneas `IMG_2041.jpg → «…»` |
| `proyectos_vision.png` | Criterio 7 | Proyectos propuestos y vista previa |
| `inyeccion.png` | Criterio 3 o 7 | El archivo "IGNORA LAS INSTRUCCIONES…" quedó como un archivo más |
| `fechas.png` | Criterio 6 | `Fecha de la cámara (EXIF): 43` y carpetas 2023/2024/2025 |
| `simular.png` | SIMULAR | Se copiarían, duplicados, espacio |
| `final.png` | CREAR COPIAS | `FINALIZADO` con errores 0 y originales modificados 0 |
| `despues.png` | `tree -d Descargas_demo_NEXORA_*/ORGANIZADOS` | El árbol ordenado |
| `foto_original.png` | Abrir `IMG_2041.jpg` en el visor | Para mostrar que la foto sigue intacta |

Para anotar en el guion: cuántas fotos vio Qwen, cuánto tardó y 2 o 3 descripciones textuales.

## 3. Antes de publicar

- [ ] Ninguna captura muestra `/home/…`, `/Users/…`, `C:\Users\…` ni tu nombre de usuario.
- [ ] Ninguna muestra archivos reales tuyos (solo `Descargas_demo`).
- [ ] La barra de título y el prompt no muestran `usuario@equipo`.

## 4. Limpiar

```bash
python3 demo/crear_carpeta_demo.py --borrar   # borra ~/NEXORA_DEMO y las copias que NEXORA creó dentro
```

## Organización sugerida del proyecto del video

```
~/pieza-por-pieza/
├── nexora/                      ← este repositorio (la app)
├── pieza-por-pieza-motor/       ← el motor 3D
│   └── videos/nexora_largo, nexora_s1 … nexora_s5
└── grabacion/nexora/
    ├── capturas/                ← los .png de la tabla de arriba
    ├── voz/                     ← largo.wav, s1.wav … s5.wav
    └── notas.md                 ← cifras reales (fotos vistas, tiempos, descripciones)
```
