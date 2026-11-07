#!/usr/bin/env python3
"""Evaluación offline: nunca envía el manifiesto al modelo."""
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

LAB = Path.home() / 'pieza-lab-20261105'
CATS = {'universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos'}

def require(cond, msg):
    if not cond:
        raise SystemExit('ERROR: ' + msg)

with (LAB/'reference/manifest.json').open(encoding='utf-8') as f:
    manifest = json.load(f)['files']
truth = {}
for item in manifest:
    name = item['nombre']
    require(name not in truth, 'nombre duplicado en manifiesto')
    truth[name] = item
require(len(truth) == 1000, 'manifiesto no contiene 1000 nombres únicos')

with (LAB/'baseline_predictions.csv').open(newline='',encoding='utf-8') as f:
    baseline = list(csv.DictReader(f))
require(len(baseline) == 1000, 'baseline no contiene 1000 filas')
base_names = [r['nombre'] for r in baseline]
require(len(set(base_names)) == 1000 and set(base_names) == set(truth), 'nombres del baseline no coinciden con manifiesto')
ambiguous = {r['nombre'] for r in baseline if r['prediccion'] == 'ABSTENERSE'}
require(len(ambiguous) == 90, 'baseline no tiene 90 abstenciones')

with (LAB/'r5_piloto.json').open(encoding='utf-8') as f:
    pilot = json.load(f)
with (LAB/'r5j_predictions.jsonl').open(encoding='utf-8') as f:
    rest = [json.loads(line) for line in f if line.strip()]
require(len(pilot) == 5 and len(rest) == 85, f'esperados 5+85, obtenidos {len(pilot)}+{len(rest)}')
all_preds = pilot + rest
names = [r['nombre'] for r in all_preds]
require(len(set(names)) == 90 and set(names) == ambiguous, 'predicciones duplicadas, faltantes o fuera de las 90 abstenciones')

counts = Counter()
per_cat = {}
seconds = []
tokens = []
mode_counts = Counter()
for item in all_preds:
    name = item['nombre']
    expected = truth[name]['categoria_esperada']
    predicted = item['categoria']
    require(expected in CATS, 'categoria esperada desconocida')
    require(predicted is None or predicted in CATS, 'categoria predicha desconocida')
    require(truth[name]['dificultad'] == 'ambiguo', 'prediccion sobre caso no ambiguo')
    if not item.get('json_valido'):
        outcome = 'json_invalido'
    elif predicted is None:
        outcome = 'abstencion'
    elif predicted == expected:
        outcome = 'correcta'
    else:
        outcome = 'incorrecta'
    counts[outcome] += 1
    per_cat.setdefault(expected, Counter())[outcome] += 1
    if isinstance(item.get('segundos'), (int,float)):
        seconds.append(item['segundos'])
    if isinstance(item.get('tokens'), dict) and isinstance(item['tokens'].get('total_tokens'), int):
        tokens.append(item['tokens']['total_tokens'])
    if 'modo_lectura' in item:
        mode_counts[item['modo_lectura']] += 1

# Baseline correcto en 910 casos, según evaluación previa; se verifica nuevamente.
base_correct = 0
base_wrong = 0
for row in baseline:
    if row['nombre'] in ambiguous:
        continue
    if row['prediccion'] == truth[row['nombre']]['categoria_esperada']:
        base_correct += 1
    else:
        base_wrong += 1
require(base_correct + base_wrong == 910, 'conteo baseline inconsistente')

report = {
    'esquema': 'ppp_r5j_eval_v1',
    'total_dataset': 1000,
    'baseline': {'correctas':base_correct,'incorrectas':base_wrong,'abstenciones':90},
    'qwen_sobre_ambiguos': {'total':90, **{k:counts[k] for k in ('correcta','incorrecta','abstencion','json_invalido')}, 'exactitud_total':counts['correcta']/90},
    'hibrido': {'correctas':base_correct+counts['correcta'], 'incorrectas':base_wrong+counts['incorrecta'], 'abstenciones':counts['abstencion'], 'json_invalidos':counts['json_invalido'], 'exactitud_total':(base_correct+counts['correcta'])/1000},
    'por_categoria_esperada': {k:dict(v) for k,v in sorted(per_cat.items())},
    'inferencia': {'segundos_total_registrados':round(sum(seconds),3), 'segundos_media':round(statistics.mean(seconds),3) if seconds else None, 'tokens_totales_registrados':sum(tokens), 'modos_lectura_R5J':dict(mode_counts)},
    'advertencias': ['Datos sintéticos; no extrapolar a documentos reales.', 'Algunos archivos binarios no fueron interpretados.', 'Los tiempos no incluyen necesariamente preparación ni evaluación.']
}
out = LAB/'r5j_evaluacion.json'
with out.open('x',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
    f.write('\n')
print('=== RESULTADO R5-J ===')
print('Qwen (90 ambiguos):', dict(counts))
print('Exactitud Qwen ambiguos:', f"{100*counts['correcta']/90:.1f}%")
print('Híbrido:', report['hibrido'])
print('Latencia media:', report['inferencia']['segundos_media'], 's')
print('Reporte:', out.name)
