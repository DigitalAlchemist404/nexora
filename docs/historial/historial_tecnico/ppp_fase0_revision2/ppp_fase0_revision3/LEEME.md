# Pieza por Pieza — inspección R3

Ejecutar en GX10, con llama-server habitual encendido:

```bash
bash inspeccionar.sh
```

Solo requiere Bash y Python 3.9+. No instala, descarga, envía solicitudes al modelo, inicia contenedores ni modifica configuraciones. Crea una carpeta nueva al lado del script con RESUMEN_COMPARTIBLE_R3.json. Consultar la ayuda con --help.

Consulta la ayuda de ejecutables llama-server que ya corren bajo el mismo usuario. Intenta asociarlos al socket IPv4 127.0.0.1:8080 leyendo /proc; no muestra PIDs ni rutas. La falta de asociación puede deberse a permisos, namespaces u otra dirección de escucha; no demuestra ausencia de servidor.

Inspecciona metadatos de hasta 30 identificadores únicos de imágenes locales. Solo exporta ID corto, arquitectura, sistema, cantidad de volúmenes y nombres conocidos de intérpretes mencionados en Cmd/Entrypoint. No exporta etiquetas, repositorios, variables de entorno, argumentos libres ni rutas. No ejecuta esas imágenes. La mención de Python no prueba su instalación ni que una imagen sea confiable.

La ayuda seleccionada del motor se filtra para ocultar HOME, usuario, rutas, URL y correos. Este filtro no es una garantía absoluta para texto arbitrario: revisar el resumen antes de compartir. No lee argumentos del proceso ni variables de entorno del servidor.

Cuatro pruebas de desarrollo pasaron: separación de bloques de ayuda, filtrado de ejemplos privados, asociación de socket con datos sintéticos y lista permitida de metadatos. También se validaron sintaxis Bash y --help. Ninguna prueba afirma verificar la GX10 ni aislamiento real.

Siguiente paso: usar las descripciones reales de flags para diseñar comparación de razonamiento; escoger una imagen local apropiada y verificar restricciones con archivos sintéticos. No cambiar --no-reasoning-preserve suponiendo que desactiva generación de razonamiento.
