#!/usr/bin/env python3
"""Evaluador separado: solo este proceso abre el manifiesto privado."""
import argparse,csv,json,collections
from pathlib import Path
CATEGORIES={'universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--predictions',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 dest=Path(a.output).absolute()
 if dest.exists():p.error('Reporte ya existe; no sobrescribimos')
 truth=json.loads(Path(a.manifest).read_text(encoding='utf-8'))['files']
 expected={r['nombre']:r for r in truth}
 with open(a.predictions,encoding='utf-8',newline='') as fp:rows=list(csv.DictReader(fp))
 predicted={}
 for row in rows:
  name=row['nombre'];cat=row['prediccion']
  if name in predicted:p.error(f'Prediccion duplicada: {name}')
  if cat not in CATEGORIES|{'ABSTENERSE'}:p.error(f'Etiqueta invalida: {cat}')
  predicted[name]=cat
 if set(expected)!=set(predicted):p.error(f'Nombres faltantes: {len(set(expected)-set(predicted))}; extra: {len(set(predicted)-set(expected))}')
 n=len(expected);covered=sum(x!='ABSTENERSE' for x in predicted.values())
 correct=sum(predicted[name]==row['categoria_esperada'] for name,row in expected.items())
 by_difficulty={}
 for d in sorted({r['dificultad'] for r in truth}):
  subset=[r for r in truth if r['dificultad']==d]
  by_difficulty[d]={'total':len(subset),'correctas':sum(predicted[r['nombre']]==r['categoria_esperada'] for r in subset),'abstenciones':sum(predicted[r['nombre']]=='ABSTENERSE' for r in subset)}
 report={'total':n,'correctas':correct,'incorrectas':covered-correct,'abstenciones':n-covered,'cobertura':covered/n,'exactitud_total_con_abstenciones_como_no_acierto':correct/n,'precision_sobre_clasificados':correct/covered if covered else None,'por_dificultad':by_difficulty,'advertencia':'Dataset sintetico con etiquetas explicitas en muchos nombres y contenidos; no extrapolar a archivos reales.'}
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
