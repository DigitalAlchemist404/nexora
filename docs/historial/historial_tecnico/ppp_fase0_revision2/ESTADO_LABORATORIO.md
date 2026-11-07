# Estado del laboratorio — 2026-11-05

## Alcance autorizado
Fase 0 y comprobaciones pequeñas. No implementación masiva, instalaciones, descargas, exposición externa ni publicación.

## Evidencia local recibida del propietario
El RESUMEN_COMPARTIBLE.json de revisión 1 reporta dos respuestas JSON y contratos válidos, sin comillas simples externas, ambas con finish_reason stop. Tiempos 28.852 y 28.568 segundos; 1880 tokens de salida y 6404 caracteres de razonamiento en cada una; hashes finales idénticos. Los resultados no prueban aplicación efectiva de response_format. Podman reportó rootless=true y cgroups v2. Aislamiento no probado.

Modelo inicial y motor seleccionados por Anexo A: Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf; llama.cpp build 12052, commit 84d9ce0fa. Conservar archivo y binario existentes. MTP fuera de línea base. Este paquete no verifica integridad del modelo ni identidad del proceso que responde al puerto.

## Entrega actual
- auditar.sh: entrada Bash con ayuda y permisos privados.
- auditar.py: contrastes, lotes optativos e inventario mínimo.
- test_auditar.py: cinco pruebas de desarrollo, aprobadas con servidor simulado.
- LEEME.md: instrucciones, límites y privacidad.

No se ejecutaron pruebas reales de inferencia, GPU ni Podman en la GX10 desde este entorno.

## Siguiente acción
Ejecutar bash auditar.sh --lotes en la GX10 y revisar RESUMEN_COMPARTIBLE_R2.json. Después decidir prueba de control de razonamiento y escoger explícitamente una imagen local adecuada para probar aislamiento. Ninguna imagen se ejecuta por descubrirla en el inventario. La generación del dataset sigue pendiente; no está incluida en este paquete.
