#!/usr/bin/env python3
"""Create harmless synthetic demonstration files, without touching existing files."""
import argparse
import hashlib
import json
from pathlib import Path

SAMPLES = [
    ("universidad", "Resumen de una clase sobre algoritmos y estructuras de datos."),
    ("finanzas", "Presupuesto mensual ficticio: ingresos 2000, gastos 1400."),
    ("programacion", "Ejemplo de Python: una función suma dos números enteros."),
    ("trabajo", "Agenda ficticia para la reunión del equipo de proyectos."),
    ("ciencia", "Notas de laboratorio sobre temperatura y presión."),
    ("entretenimiento", "Lista ficticia de películas para ver el sábado."),
    ("fotografias", "Descripción de fotografías de un paisaje de montaña."),
    ("miscelaneos", "Recordatorio doméstico: revisar las medidas de una cortina."),
    (None, "Preparar material para la presentación."),
    (None, "Confirmar la entrega del informe."),
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="demo_publica")
    args = p.parse_args()
    root = Path(args.out)
    if root.exists():
        raise SystemExit("La carpeta destino ya existe. No se sobrescribe nada.")
    root.mkdir(parents=True)
    manifest = []
    for idx in range(30):
        label, content = SAMPLES[idx % len(SAMPLES)]
        name = f"archivo_{idx+1:03d}.txt"
        body = f"Documento de demostración {idx+1:03d}.\n{content}\n"
        (root / name).write_text(body, encoding="utf-8")
        manifest.append({"archivo": name, "categoria_ilustrativa": label, "sha256": hashlib.sha256(body.encode()).hexdigest()})
    (root / "MANIFIESTO_DEMO.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Demo creada: {len(manifest)} archivos sintéticos. No se movieron archivos personales.")

if __name__ == "__main__":
    main()
