# NEXORA R4 — Candidata de aplicación de copias

Ejecutar: `python3 iniciar.py` y elegir opción **9**.

- **Personal:** conserva nombres originales en copias; manifiesto privado con rutas relativas.
- **Anónimo:** cambia nombres de copias por IDs, NO anonimiza el contenido.
- **IA local:** requiere `llama-server` en 127.0.0.1:8080, con thinking desactivado en la solicitud.
- **Solo extensiones:** funciona sin IA; clasificación aproximada.
- Archivos desconocidos o binarios se envían a `Revisar`, nunca se ejecutan.
- Los originales no se mueven, borran ni renombran. La salida es una carpeta NUEVA fuera del origen.
- Hasta 1000 archivos, 100 MiB por archivo, 1 GiB total. Enlaces simbólicos, archivos ocultos y rutas sensibles se omiten.
- Conflictos de nombres se resuelven con sufijos, sin sobrescribir. Se verifican hashes SHA-256.
- No se recomienda borrar los originales: revisá las copias y mantené respaldo.
- La precisión de la IA NO está medida; categorías de baja confianza o discrepantes se envían a Revisar.
- **No es una versión auditada para datos críticos.** Probá primero con archivos no sensibles y respaldados.

La opción 9 es el flujo nuevo. Las opciones 7 y 8 mantienen su comportamiento de laboratorio.
