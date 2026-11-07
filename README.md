# NEXORA — Tu organizador inteligente de archivos

**Proyecto de Pieza por Pieza.** Tus archivos, en orden. Tus decisiones, bajo control.

NEXORA ordena **copias** de una carpeta con una IA que corre en tu compu (Qwen3.6 + llama.cpp). Nunca mueve, borra ni renombra los originales, y nada sale a internet.

## Empezar (Python 3.9+, sin dependencias)

| Sistema | Comando |
|---------|---------|
| Linux · macOS (Intel o Apple Silicon) | `python3 iniciar.py` |
| Windows | `py iniciar.py` |

1. **Opción 1:** elige tu GGUF y tu `llama-server` (busca también en LM Studio y Homebrew). Si junto al modelo hay un `mmproj-*.gguf`, ofrece activar la **visión**. La próxima vez recuerda tu elección: basta con Enter.
2. **Opción 2:** espera a que diga `Listo` (o `Listo (con visión)`).
3. **Opción 9:** elige la carpeta y el criterio, revisa la vista previa, escribe **SIMULAR** y luego **CREAR COPIAS**.

¿Primera vez? Crea una carpeta de prueba ficticia: `python3 demo/crear_carpeta_demo.py` (ver más abajo).

## Criterios de la opción 9

| # | Criterio | Resultado | IA |
|---|----------|-----------|----|
| 1 | Por tipo | `Imagenes/`, `Videos/`, `Documentos/`… | No |
| 2 | Por tipo + Qwen revisa textos | Igual, y Qwen confirma .txt/.md/.py/.json | Sí (lee texto) |
| 3 | Por proyecto | `Vacaciones_Playa/Imagenes/`… | Sí (lee **solo nombres**) |
| 4 | Por carpeta de origen | `Nueva carpeta/Imagenes/`… | No |
| 5 | Por fecha del archivo | `2026/2026-11/Imagenes/`… | No |
| 6 | Por fecha en que se tomó la foto | `2024/2024-07/Imagenes/`… (EXIF; si no hay, fecha del archivo) | No |
| 7 | Por lo que muestran fotos y videos | `Vacaciones/Imagenes/`… | Sí (Qwen **mira** cada imagen y un fotograma de cada video) |

**Siempre:**
- Verifica cada copia con SHA-256.
- Copia una sola vez los duplicados exactos.
- Manda a `Revisar` lo que genera dudas, con el motivo.
- Omite los ocultos, los enlaces y los nombres sensibles (contraseñas, secretos, pasaporte, `.env`…).
- Antes de copiar, revisa que haya espacio libre.

**Visión (criterio 7):**
- Las imágenes se reducen a 640 px **en memoria**, con Pillow, ffmpeg o sips (macOS).
- Solo se envían a 127.0.0.1.
- Límite: 400 por corrida.
- Lo que Qwen vio queda en `MANIFIESTO_PRIVADO.json` (`qwen_vio`).

**Límites:** 1000 archivos, 100 MiB por archivo y 1 GiB en total por corrida.

## Carpeta de prueba ficticia

```bash
python3 demo/crear_carpeta_demo.py            # crea ~/NEXORA_DEMO/Descargas_demo (71 archivos, 2,9 MB)
python3 demo/crear_carpeta_demo.py --rehacer  # la vuelve a crear desde cero
python3 demo/crear_carpeta_demo.py --borrar   # borra ~/NEXORA_DEMO entera, incluidas las copias de NEXORA
```

Todo es inventado:
- Las fotos son dibujos hechos por código (`demo/generar_recursos.py`), con fecha de cámara ficticia.
- Las tareas, recetas y gastos son de ejemplo.
- Tiene duplicados, `contraseñas_wifi.txt` (debe quedar **omitido**) y un archivo cuyo nombre intenta darle órdenes a la IA.

## Grabar un video

En la opción 4 → 5, el **modo grabación** reemplaza tu carpeta personal por `~` y oculta tu usuario. La guía completa está en [`docs/GRABACION.md`](docs/GRABACION.md).

## Estructura

```
iniciar.py               ← entrada
pieza_por_pieza/         ← la aplicación (cli, organizador, agrupador, visión, servidor, modelos)
tests/                   ← pruebas automáticas
demo/                    ← carpeta de prueba ficticia (script + recursos dibujados)
docs/CAMBIOS.md          ← qué cambió en cada versión
docs/GRABACION.md        ← cómo grabar sin mostrar datos personales
docs/historial/          ← investigación previa (R3, R4, fases, laboratorio R5)
```

## Pruebas

```bash
python3 -m unittest discover -s tests -v
python3 docs/historial/historial_tecnico/PPP_R5R2/test_r5r2.py
```

## Alcance y seguridad

Es una beta, no un lanzamiento auditado. Prueba primero con la carpeta ficticia y después con archivos respaldados. La opción 6 (demostración reversible con 30 archivos sintéticos) y las 7–8 son del laboratorio previo. El servidor escucha en 127.0.0.1:8080; revisa las advertencias de seguridad de llama.cpp. No publiques `MANIFIESTO_PRIVADO.json` ni los registros locales.

Licencia: [MIT](LICENSE). llama.cpp (MIT) y Qwen3.6 (Apache 2.0) no se incluyen: cada uno tiene su propia licencia.
