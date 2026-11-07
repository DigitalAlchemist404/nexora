# Pieza por Pieza — Fase 0, revisión 2

Paquete de diagnóstico, no organizador de archivos. No instala, descarga, publica, reinicia el servidor, activa MTP ni mueve el modelo. Requiere Bash y Python 3.9+; el entorno objetivo tiene Python 3.12.3.

## Uso en la GX10

Descomprimir el ZIP en una carpeta nueva. Abrir una terminal en `ppp_fase0_revision2` y mantener el servidor habitual escuchando en 127.0.0.1:8080.

```bash
bash auditar.sh --lotes
```

Hace cuatro solicitudes de contraste y, solo si resultan positivas, hasta tres solicitudes de lotes (5/20/50). Límite de 2048 tokens por contraste y 4096 por lote, 180 segundos de espera de socket por solicitud. Este último no constituye un límite absoluto si el servidor transmite lentamente. El script no cancela trabajos internos del servidor tras un timeout. No ejecutar varias copias simultáneas. Puede tardar varios minutos; Ctrl+C interrumpe y conserva el resumen disponible y los originales ya escritos.

Cada ejecución crea un directorio nuevo junto al script; no sobrescribe corridas previas. Compartir únicamente `RESUMEN_COMPARTIBLE_R2.json`. Las solicitudes y respuestas originales quedan en `privado/`, con permisos privados. No subir esa carpeta: el servidor podría incluir datos internos. No se imprimen rutas, nombres de imágenes, comandos del servidor ni respuestas libres del modelo.

Opciones:

```bash
bash auditar.sh --help
bash auditar.sh                    # Cuatro contrastes, sin lotes
bash auditar.sh --solo-inventario  # Sin inferencia
```

## Qué verifica

- Dos pares control/esquema, con semillas 42 y 43. Dentro de cada par el prompt es idéntico y pide PROMPT; el esquema exige ESQUEMA_1 o ESQUEMA_2, ausentes del prompt. Se requiere que el control cumpla el prompt y el ensayo restringido cumpla el esquema.
- Se rechazan JSON con claves duplicadas, constantes no estándar o texto externo. No se limpia el contenido silenciosamente.
- Los lotes comprueban identificadores exactos, ausencia de duplicados, categorías permitidas y finalización. Se detienen ante el primer lote incompleto. Son cargas repetitivas exploratorias, no el dataset definitivo ni un benchmark de calidad general.
- Inventario de IDs de imágenes locales de Podman, sin arrancarlas o descargarlas.
- Opciones anunciadas por ejecutables llama-server ya activos bajo el mismo usuario mediante --help/--version. No se modifica su configuración. Se omite un motor que no pueda inspeccionarse. No se asocia de forma concluyente ese ejecutable al puerto 8080.

El cliente rechaza proxies y redirecciones; consulta únicamente loopback. La lista de flags no prueba que un parámetro funcione. Dos contrastes positivos son evidencia de comportamiento, no prueba del mecanismo interno (gramática frente a inyección de esquema en plantilla) ni soporte universal de JSON Schema. No se ha verificado aislamiento ni uso de herramientas.

## Validación del paquete

Cinco pruebas automáticas pasaron en el entorno de desarrollo: JSON estricto, contrato de lotes, servidor simulado que respeta esquema, servidor simulado que lo ignora y rechazo de redirecciones. Sintaxis Bash y ayuda verificadas. Los servidores de esas pruebas son simulaciones explícitas: NO son resultados de la GX10 ni de Qwen.

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

El código se entrega para revisión y uso en el laboratorio. La licencia pública definitiva se incorporará al crear el repositorio con su titular correspondiente.

Esto es Pieza por Pieza: una idea pequeña, algo extraordinario.
