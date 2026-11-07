#!/usr/bin/env python3
"""R5-Q: simulador de decisiones seguras, sin operaciones de archivos del dataset."""
import argparse, csv, hashlib, json
from collections import Counter
from pathlib import Path

CATEGORIES = {'universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos'}
ROOT = Path.home() / 'pieza-lab-r5p-20261105'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    root=args.root.expanduser().resolve()
    output=(args.output.expanduser() if args.output else root/'r5q_simulacion').resolve()
    if output == root or output == root/'dataset' or output.is_relative_to(root/'dataset') or output.is_relative_to(root/'reference'):
        ap.error('La salida no puede estar dentro del dataset ni de reference.')
    source=root/'r5p2_predictions.jsonl'
    dataset=root/'dataset'
    if not source.is_file(): ap.error(f'No se encontraron predicciones en {source}; usá --root con el laboratorio correcto.')
    if not dataset.is_dir(): ap.error('No se encontró el dataset.')
    entries=[]
    for line_no,line in enumerate(source.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        try: rec=json.loads(line)
        except json.JSONDecodeError: ap.error(f'JSONL inválido en línea {line_no}')
        entries.append(rec)
    if len(entries)!=48: ap.error(f'Se esperaban 48 predicciones, hay {len(entries)}. No se generó salida.')
    seen=set(); rows=[]
    for rec in entries:
        name=rec.get('nombre')
        if not isinstance(name,str) or not name or Path(name).name != name or name in {'.','..'} or '/' in name or '\\' in name or name in seen:
            ap.error('Nombre duplicado, ausente o no seguro en las predicciones.')
        seen.add(name)
        file=dataset/name
        if file.is_symlink() or not file.is_file(): ap.error('Archivo faltante o enlace simbólico en el dataset.')
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if digest != rec.get('sha256'): ap.error('Hash no coincide con la predicción guardada; abortando.')
        category=rec.get('categoria')
        valid_json=rec.get('json_valido') is True
        if not valid_json:
            state='BLOQUEADO_JSON_INVALIDO'; candidate=''
        elif category is None:
            state='ABSTENCION_SIN_ACCION'; candidate=''
        elif not isinstance(category,str) or category not in CATEGORIES:
            state='BLOQUEADO_CATEGORIA'; candidate=''
        else:
            state='PROPUESTA_PENDIENTE_APROBACION'; candidate=category
        rows.append({'id':hashlib.sha256((name+'\0'+digest).encode()).hexdigest()[:16], 'archivo':name, 'sha256':digest, 'categoria_propuesta':candidate, 'estado':state, 'aprobado':False, 'movimiento_ejecutado':False})
    if output.exists(): ap.error('La carpeta de salida ya existe. No se sobrescribirá; usá --output RUTA_NUEVA.')
    output.mkdir(parents=True)
    counts=Counter(r['estado'] for r in rows)
    summary={'fase':'R5-Q','origen':'R5-P.2','total':len(rows),'estados':dict(sorted(counts.items())), 'aprobaciones':0,'movimientos':0,'modo':'simulacion_sin_escritura_en_dataset','nota':'Una propuesta válida no implica categoría correcta ni permiso para mover.'}
    with (output/'propuestas.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (output/'resumen.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('=== R5-Q SIMULACION SEGURA ===')
    print('Predicciones verificadas:',len(rows))
    for state,n in sorted(counts.items()): print(state+':',n)
    print('Aprobaciones: 0 | Movimientos: 0')
    print('Salida:',output)
    print('IMPORTANTE: no se evaluó la corrección semántica de cada propuesta; no se ejecutaron movimientos.')

if __name__=='__main__': main()
