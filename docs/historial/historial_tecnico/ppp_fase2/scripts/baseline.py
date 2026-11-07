#!/usr/bin/env python3
"""Baseline conservador por nombre; NO usa manifiesto ni lee contenidos."""
import argparse,csv,json,time
from pathlib import Path
CATEGORIES=('universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos')
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 root=Path(a.dataset).resolve(strict=True); out=Path(a.output).absolute()
 if not root.is_dir():p.error('dataset no es directorio')
 if out==root or root in out.parents:p.error('Salida debe quedar fuera del dataset')
 if out.exists():p.error('La salida ya existe; no sobrescribimos')
 start=time.perf_counter();rows=[]
 for f in sorted(root.iterdir()):
  if not f.is_file() or f.is_symlink():p.error('Solo archivos regulares en raiz')
  cat=next((c for c in CATEGORIES if f.name.startswith(c+'_')),None)
  rows.append({'nombre':f.name,'prediccion':cat if cat else 'ABSTENERSE','metodo':'prefijo_nombre' if cat else 'sin_pista'})
 if len(rows)!=1000:p.error(f'Se esperaban 1000 archivos; hay {len(rows)}')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x',encoding='utf-8',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=['nombre','prediccion','metodo']);w.writeheader();w.writerows(rows)
 elapsed=time.perf_counter()-start
 print(json.dumps({'archivos':len(rows),'predicciones':sum(x['prediccion']!='ABSTENERSE' for x in rows),'abstenciones':sum(x['prediccion']=='ABSTENERSE' for x in rows),'segundos':round(elapsed,6),'salida':str(out)},ensure_ascii=False))
if __name__=='__main__':main()
