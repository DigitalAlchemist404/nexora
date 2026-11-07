#!/usr/bin/env python3
"""R5-M: inspeccion local y de solo lectura del error TXT de R5-L.2."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path.home() / 'pieza-lab-r5l-20261106'

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mostrar-contenido', action='store_true', help='Muestra hasta 3000 caracteres del TXT solo en tu terminal local')
    args = ap.parse_args()
    manifest_path = ROOT / 'reference' / 'manifest.json'
    predictions_path = ROOT / 'r5l2_predictions.jsonl'
    dataset = ROOT / 'dataset'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    records = manifest['files'] if isinstance(manifest, dict) else manifest
    truth = {row['nombre']: row for row in records}
    if len(truth) != len(records):
        raise SystemExit('ERROR: nombres duplicados en manifiesto')
    predictions = {}
    for line in predictions_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        name = row['nombre']
        if name in predictions:
            raise SystemExit('ERROR: prediccion duplicada')
        predictions[name] = row
    if len(predictions) != 72 or len(truth) != 72 or set(predictions) != set(truth):
        raise SystemExit('ERROR: no hay correspondencia completa de 72 archivos')
    errors = []
    for name, prediction in predictions.items():
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise SystemExit('ERROR: ruta insegura')
        file = dataset / rel
        if not file.is_file() or file.is_symlink() or file.resolve().parent != dataset.resolve():
            raise SystemExit('ERROR: archivo ausente o ruta inesperada')
        digest = sha256(file)
        if digest != prediction['sha256'] or digest != truth[name]['sha256']:
            raise SystemExit('ERROR: hash diferente; auditoria suspendida')
        if prediction['json_valido'] and prediction['categoria'] is not None and prediction['categoria'] != truth[name]['categoria_esperada']:
            errors.append((name, prediction, truth[name], file))
    print('=== R5-M AUDITORIA SOLO LECTURA ===')
    print('Predicciones verificadas:', len(predictions))
    print('Errores encontrados:', len(errors))
    for i, (name, prediction, reference, file) in enumerate(errors, 1):
        content = file.read_text(encoding='utf-8')
        print(f'\n=== ERROR {i} ===')
        print('Formato:', file.suffix.lower().lstrip('.'))
        print('Categoria predicha:', prediction['categoria'])
        print('Categoria esperada:', reference['categoria_esperada'])
        print('Tamano en caracteres:', len(content))
        print('Latencia (s):', prediction['segundos'])
        print('Tokens:', prediction['tokens'])
        print('Nombre contiene categoria esperada:', reference['categoria_esperada'].casefold() in name.casefold())
        print('Nombre contiene categoria predicha:', prediction['categoria'].casefold() in name.casefold())
        print('Contenido contiene categoria esperada:', reference['categoria_esperada'].casefold() in content.casefold())
        print('Contenido contiene categoria predicha:', prediction['categoria'].casefold() in content.casefold())
        if args.mostrar_contenido:
            print('Nombre:', name)
            print('--- CONTENIDO (MAXIMO 3000 CARACTERES) ---')
            print(content[:3000])
            print('--- FIN ---')
    print('\nNota: las coincidencias de palabras no prueban causalidad.')
    print('No se ejecutaron modelos ni se modificaron archivos.')
    print('No compartas contenido o nombres sin revisarlos antes.')

if __name__ == '__main__':
    main()
