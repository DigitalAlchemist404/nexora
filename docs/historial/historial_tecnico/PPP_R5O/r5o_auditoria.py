#!/usr/bin/env python3
"""R5-O: auditoría local, solo lectura, de las discrepancias de R5-N."""
import argparse, json, csv
from pathlib import Path
from collections import Counter

ROOT = Path.home() / 'pieza-lab-r5n-20261106'

def load_records(path):
    if path.suffix == '.jsonl':
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if path.suffix == '.csv':
        with path.open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, list): return data
    for k in ('predicciones','predictions','registros','records','files','casos'):
        if isinstance(data.get(k), list): return data[k]
    raise ValueError('No se encontró lista de registros')

def choose(d, *keys):
    for k in keys:
        if k in d: return d[k]
    return None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--predicciones', type=Path, help='Ruta explícita al archivo de predicciones R5-N')
    p.add_argument('--mostrar-contenido', action='store_true', help='Muestra textos locales; revisar antes de compartir')
    args=p.parse_args()
    root=args.root.expanduser()
    manifest=root/'reference'/'manifest.json'
    if not manifest.is_file():
        raise SystemExit(f'No encontré manifiesto en {manifest}. Usá --root RUTA_CORRECTA')
    m=json.loads(manifest.read_text(encoding='utf-8'))
    refs= m if isinstance(m,list) else choose(m,'files','casos','records')
    if not isinstance(refs,list) or not refs:
        raise SystemExit('Formato de manifiesto no reconocido.')
    candidates = sorted([x for x in root.glob('**/*') if x.is_file() and x.suffix in ('.jsonl','.csv','.json') and 'reference' not in x.parts and 'dataset' not in x.parts and ('pred' in x.name.lower() or 'resultado' in x.name.lower())])
    if args.predicciones:
        predpath=args.predicciones.expanduser()
    elif len(candidates)==1:
        predpath=candidates[0]
    else:
        print('Archivos candidatos de predicciones:')
        for x in candidates: print(' -',x.relative_to(root))
        raise SystemExit('Indicá --predicciones RUTA_AL_ARCHIVO para evitar elegir incorrectamente.')
    preds=load_records(predpath)
    print('=== R5-O AUDITORIA SOLO LECTURA ===')
    print('Campos de referencia:',sorted(refs[0]))
    print('Campos de predicción:',sorted(preds[0]) if preds else [])
    def name(r): return choose(r,'nombre','filename','name','archivo','ruta_original','path')
    truth={}
    for r in refs:
        n=name(r)
        if not n or n in truth: raise SystemExit('Nombre faltante o duplicado en referencia.')
        truth[n]=r
    seen=set(); discrepancies=[]; counts=Counter()
    for r in preds:
        n=name(r)
        if not n or n in seen or n not in truth: raise SystemExit('Predicción duplicada, sin nombre o sin referencia.')
        seen.add(n)
        ref=truth[n]
        typ=str(choose(ref,'tipo','tipo_caso','dificultad','claridad') or '').lower()
        expected=choose(ref,'categoria_esperada','categoria','category','label')
        prediction=choose(r,'categoria','prediccion','predicted_category','category')
        if isinstance(prediction,str) and prediction.strip().lower() in ('null','none','abstenerse','abstencion',''):
            prediction=None
        # Some datasets may specify expected behavior rather than a category for ambiguous cases.
        expected_behavior=str(choose(ref,'comportamiento_esperado','accion_esperada','resultado_esperado') or '').lower()
        if typ not in ('claro','ambiguo'):
            raise SystemExit('No identifico tipo claro/ambiguo en referencia. Revisá los campos mostrados.')
        if typ=='claro':
            status='correcta' if prediction==expected else ('abstencion' if prediction is None else 'incorrecta')
        else:
            status='abstencion' if prediction is None else 'clasificacion_ambigua'
        counts[(typ,status)]+=1
        if (typ=='claro' and status!='correcta') or (typ=='ambiguo' and status!='abstencion'):
            discrepancies.append((n,typ,expected,prediction,status,r))
    if len(seen)!=len(truth):
        raise SystemExit(f'Cobertura incompleta: {len(seen)}/{len(truth)}; no emitir diagnóstico parcial como completo.')
    print('Total:',len(seen))
    print('Resumen:',{f'{k[0]}:{k[1]}':v for k,v in sorted(counts.items())})
    print('Discrepancias:',len(discrepancies))
    for i,(n,typ,expected,prediction,status,r) in enumerate(discrepancies,1):
        print(f'\n--- CASO {i} ---')
        print('Tipo:',typ,'| Estado:',status)
        print('Referencia:',expected,'| Predicción:',prediction)
        reason=choose(r,'justificacion','justificación','razon','razón','motivo','reason','respuesta')
        if reason is not None:
            s=str(reason)
            print('Justificación/respuesta registrada (revisar antes de compartir):',s[:700])
        if args.mostrar_contenido:
            path=root/'dataset'/n
            if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to((root/'dataset').resolve()):
                print('Contenido:',path.read_text(encoding='utf-8',errors='replace')[:1500])
            else: print('Contenido no disponible o ruta no segura')
    print('\nNo se modificaron archivos ni se ejecutaron modelos.')

if __name__=='__main__': main()
