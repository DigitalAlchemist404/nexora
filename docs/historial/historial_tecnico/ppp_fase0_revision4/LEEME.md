# Pieza por Pieza — R4: configuración actual frente a reasoning off

Requiere la GX10 Linux, Python 3.12 y el servidor habitual build 12052 activo en 127.0.0.1:8080. Descomprimir en carpeta nueva. No ejecutar varias copias del diagnóstico ni otros clientes de inferencia durante las medidas.

## Tres comandos

En la carpeta del paquete, manteniendo el servidor habitual activo:

```bash
bash comparar.sh base
```

Identifica el proceso por socket, guarda su comando original y un subconjunto de su entorno en `privado/config_original.json`, calcula SHA256 del binario (no del modelo), y mide lotes 5/20/50. Nunca compartir privado: incluye rutas personales, configuración y respuestas originales.

Cuando la base termine correctamente, ir a la terminal de llama-server y detenerlo con Ctrl+C. Volver a esta carpeta:

```bash
bash comparar.sh off
```

Arranca el mismo binario con los mismos argumentos, sustituyendo solo la opción de razonamiento por `--reasoning off`. El modelo permanece en su ubicación. Comprueba que el puerto pertenece al proceso creado antes de consultar su salud. Ejecuta las mismas solicitudes y detiene su servidor al acabar. No mata procesos preexistentes; si 8080 está ocupado, se detiene con un mensaje.

Para dejar otra vez el servidor original encendido:

```bash
bash comparar.sh restaurar
```

Este último comando permanece activo; dejar la terminal abierta. Ctrl+C lo detiene. Los logs de arranque quedan privados y no se muestran por consola. Si hay varias sesiones, indicar el nombre de carpeta impreso en la ejecución base:

```bash
bash comparar.sh off --sesion ppp_fase0_r4_NOMBRE
bash comparar.sh restaurar --sesion ppp_fase0_r4_NOMBRE
```

Compartir únicamente `RESUMEN_COMPARTIBLE_R4.json` dentro de esa sesión. El informe conserva las mediciones de ambas condiciones y solo calcula un factor de tiempo cuando las solicitudes son idénticas y ambas respuestas completas.

## Límites y comportamiento

- Seis solicitudes en total (tres por condición), salvo fallo. Los lotes son exploratorios y repetitivos, no el dataset definitivo de 1000 archivos.
- Máximo 4096 tokens por solicitud, timeout de socket 180 s; este timeout no es límite total ante transmisión lenta. Un timeout del cliente no garantiza cancelar la generación del servidor original. Si ocurre, revisar y dejar terminar antes de otra prueba.
- Un lote incompleto detiene el crecimiento de tamaño. La condición off requiere las tres mediciones base completas.
- No descarga, instala, publica, modifica el modelo, cambia MTP ni inicia contenedores. Se rechaza una configuración que anuncie especulación activa.
- Se admiten exclusivamente opciones de arranque conocidas; ante argumentos no cubiertos se detiene sin imprimirlos. Se rechazan variables LLAMA_* del proceso original porque podrían cambiar la comparación. No se leen ni guardan valores fuera del subconjunto de entorno utilizado para reproducir el motor.
- La restauración reconstruye el comando, directorio de trabajo y subconjunto de entorno conservado; no promete reproducir estado de cachés, sesiones previas, límites externos del proceso ni todo el entorno de la terminal.
- La comparación es secuencial actual/off y cada tamaño se mide una vez. Caches, calentamiento y carga del equipo pueden afectar tiempos. No constituye un benchmark estadístico ni una conclusión de calidad general.
- La ausencia de reasoning_content no prueba por sí sola ausencia de cómputo interno. Revisar tokens totales, contenido, validez y aciertos conjuntamente.
- El diagnóstico no modifica aislamiento; la imagen candidata de Podman todavía no se ejecuta.
- Ctrl+C conserva los originales ya escritos. Una prueba off parcialmente escrita no se sobrescribe automáticamente. Para repetir de cero: restaurar, completar una nueva sesión base y usar su nombre explícito.

## Pruebas de desarrollo

10 pruebas automatizadas aprobadas: modificación exclusiva de argumentos de razonamiento, rechazo de opciones no admitidas, entorno controlado, comparación por hashes, manejo del proceso propio, JSON estricto, contrato de lotes, servidor simulado con esquema, servidor simulado que ignora esquema y redirecciones. Sintaxis Bash y ayuda verificadas. Estas pruebas NO ejecutaron Qwen ni el motor ARM64.

```bash
python3 -m unittest discover -s . -v
```

Esto es Pieza por Pieza: una idea pequeña, algo extraordinario.
