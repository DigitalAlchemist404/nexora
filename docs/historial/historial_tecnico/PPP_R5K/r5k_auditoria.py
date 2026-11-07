#!/usr/bin/env python3
"""R5-K: auditoria offline y sin modificar resultados previos. Solo stdlib."""
import argparse, csv, hashlib, json, re, statistics
from collections import Counter, defaultdict
from pathlib import Path

CATS = {'universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos'}

def check(ok, message):
    if not ok: raise SystemExit('ERROR: '+message)

def load(path):
    with path.open(encoding='utf-8') as f: return json.load(f)

def classify(row, expected):
    if not row.get('json_valido'): return 'json_invalido'
    if row['categoria'] is None: return 'abstencion'
    return 'correcta' if row['categoria'] == expected else 'incorrecta'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lab',type=Path,default=Path.home()/'pieza-lab-20261105')
    ap.add_argument('--out',type=Path,default=None)
    args=ap.parse_args()
    lab=args.lab.expanduser().resolve()
    out=(args.out or lab/'r5k_auditoria').expanduser().absolute()
    check(not out.exists(), 'Destino ya existe; no se sobrescribe: '+str(out))
    manifest=load(lab/'reference/manifest.json')['files']
    truth={x['nombre']:x for x in manifest}
    check(len(manifest)==1000 and len(truth)==1000,'Manifiesto incompleto o duplicado')
    with (lab/'baseline_predictions.csv').open(newline='',encoding='utf-8') as f:
        base=list(csv.DictReader(f))
    check(len(base)==1000 and len({x['nombre'] for x in base})==1000,'Baseline incompleto o duplicado')
    check({x['nombre'] for x in base}==set(truth),'Baseline no coincide con referencia')
    ambiguous={x['nombre'] for x in base if x['prediccion']=='ABSTENERSE'}
    check(len(ambiguous)==90,'Se esperaban 90 abstenciones')
    pilot=load(lab/'r5_piloto.json')
    with (lab/'r5j_predictions.jsonl').open(encoding='utf-8') as f:
        rest=[json.loads(line) for line in f if line.strip()]
    preds=pilot+rest
    check(len(pilot)==5 and len(rest)==85 and len(preds)==90,'Se esperan 5+85 predicciones')
    check({x['nombre'] for x in preds}==ambiguous and len({x['nombre'] for x in preds})==90,'Predicciones faltantes o duplicadas')
    check(all(x['categoria'] is None or x['categoria'] in CATS for x in preds),'Categoria predicha desconocida')
    counts=Counter(); by_cat=defaultdict(Counter); by_format=defaultdict(Counter); by_mode=defaultdict(Counter)
    rows=[]; risk=Counter(); seconds=[]
    for p in preds:
        name=p['nombre']; m=truth[name]; expected=m['categoria_esperada']; outcome=classify(p,expected)
        check(m['dificultad']=='ambiguo','Caso no ambiguo en predicciones')
        counts[outcome]+=1;by_cat[expected][outcome]+=1;by_format[m['formato']][outcome]+=1
        mode=p.get('modo_lectura','no_registrado');by_mode[mode][outcome]+=1
        if isinstance(p.get('segundos'),(int,float)):seconds.append(p['segundos'])
        path=lab/'dataset'/name
        check(path.is_file() and not path.is_symlink() and path.resolve().parent== (lab/'dataset').resolve(),'Archivo fuera del dataset o enlace')
        raw=path.read_bytes()
        check(hashlib.sha256(raw).hexdigest()==m['sha256'],'Hash de dataset no coincide con manifiesto')
        # Solo inspeccion literal; no interpreta ni ejecuta contenido de archivos.
        txt=raw.decode('utf-8','replace') if m['formato'] in ('txt','md','csv','json') else ''
        explicit=bool(re.search(r'(?i)\bcategoria\b\s*[:=,]\s*["\']?'+re.escape(expected)+r'\b',txt))
        if m['formato']=='pdf':
            explicit=(b'Categoria: '+expected.encode('ascii') in raw)
        if explicit:risk['categoria_explicita_en_contenido']+=1
        if m['formato']=='png':risk['png_sin_vision_en_r5j']+=1
        if mode=='binario_no_interpretado':risk['binario_no_interpretado']+=1
        rows.append({'nombre':name,'categoria_esperada':expected,'categoria_predicha':p['categoria'] or '', 'resultado':outcome,'formato':m['formato'],'modo_lectura':mode,'categoria_explicita':int(explicit),'segundos':p.get('segundos',''),'tokens_total':p.get('tokens',{}).get('total_tokens','') if isinstance(p.get('tokens'),dict) else '', 'origen':'piloto' if p in pilot else 'r5j'})
    base_ok=sum(x['prediccion']==truth[x['nombre']]['categoria_esperada'] for x in base if x['nombre'] not in ambiguous)
    base_bad=910-base_ok
    report={
        'esquema':'ppp_r5k_auditoria_v1',
        'resumen':{'ambiguous':90,'correctas':counts['correcta'],'incorrectas':counts['incorrecta'],'abstenciones':counts['abstencion'],'json_invalidos':counts['json_invalido'], 'baseline_correctas':base_ok,'baseline_incorrectas':base_bad,'hibrido_correctas':base_ok+counts['correcta'],'hibrido_incorrectas':base_bad+counts['incorrecta']},
        'por_categoria_esperada':{k:dict(v) for k,v in sorted(by_cat.items())},
        'por_formato':{k:dict(v) for k,v in sorted(by_format.items())},
        'por_modo_lectura':{k:dict(v) for k,v in sorted(by_mode.items())},
        'indicadores_fuga_etiqueta':dict(risk),
        'latencia_media_s':round(statistics.mean(seconds),3) if seconds else None,
        'advertencias':['El contenido sintetico incluye etiquetas explicitas de categoria en TXT/MD/CSV/JSON/PDF.', 'Las imagenes PNG del generador son pixeles aleatorios, no fotos semanticas.', 'No usar estos 90 casos como prueba independiente despues de ajustar el clasificador.', 'Una categoria explicita no prueba por si sola que el modelo la haya utilizado.']
    }
    out.mkdir(parents=True,exist_ok=False)
    (out/'resumen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'casos.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (out/'errores_y_abstenciones.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(x for x in rows if x['resultado']!='correcta')
    print('=== R5-K AUDITORIA OFFLINE ===')
    print('Correctas:',counts['correcta'],'| Incorrectas:',counts['incorrecta'],'| Abstenciones:',counts['abstencion'])
    print('Categoria explicita en contenido:',risk['categoria_explicita_en_contenido'],'de 90')
    print('PNG sin vision:',risk['png_sin_vision_en_r5j'],'| Binarios no interpretados:',risk['binario_no_interpretado'])
    print('=== POR FORMATO ===')
    for k,v in sorted(by_format.items()):print(k,dict(v))
    print('=== POR CATEGORIA ESPERADA ===')
    for k,v in sorted(by_cat.items()):print(k,dict(v))
    print('Reportes locales:',out)
    print('ATENCION: No publicar casos.csv sin revisar posibles datos privados de nombres.')

if __name__=='__main__':main()
