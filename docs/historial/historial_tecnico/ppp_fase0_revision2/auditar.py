#!/usr/bin/env python3
"""Diagnóstico local. Biblioteca estándar; no instalaciones ni movimientos."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

CATEGORIES = ['Universidad', 'Finanzas ficticias', 'Programacion', 'Revision']

def pairs_unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate key')
        obj[key] = value
    return obj

def bad_constant(value):
    raise ValueError('non-JSON constant')

def strict_loads(text):
    return json.loads(text, object_pairs_hook=pairs_unique, parse_constant=bad_constant)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

class Client:
    def __init__(self, port=8080):
        self.base = 'http://127.0.0.1:' + str(port)
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path, body=None):
        req = urllib.request.Request(self.base + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Content-Type': 'application/json'})
        with self.http.open(req, timeout=180) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError('response limit')
        return strict_loads(data)

def write_json(path, obj):
    # Todos los destinos están dentro de una carpeta nueva y privada.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)

def number(value):
    return value if type(value) in (int, float) and value >= 0 else None

def call(client, private, name, body):
    write_json(private / (name + '_solicitud.json'), body)
    start = time.perf_counter()
    row = {'prueba': name}
    parsed = None
    try:
        response = client.request('/v1/chat/completions', body)
        write_json(private / (name + '_respuesta.json'), response)
        choice = response['choices'][0]
        msg = choice['message']
        content = msg.get('content')
        finish = choice.get('finish_reason')
        row['fin'] = finish if finish in ('stop', 'length', 'tool_calls') else 'otro'
        reasoning = msg.get('reasoning_content')
        row['caracteres_razonamiento'] = len(reasoning) if isinstance(reasoning, str) else None
        usage = response.get('usage') or {}
        row['prompt_tokens'] = number(usage.get('prompt_tokens'))
        row['completion_tokens'] = number(usage.get('completion_tokens'))
        row['json_valido'] = False
        if isinstance(content, str):
            row['content_sha256'] = hashlib.sha256(content.encode()).hexdigest()
            try:
                parsed = strict_loads(content)
                row['json_valido'] = True
            except (ValueError, TypeError):
                pass
    except Exception as exc:
        row['error_tipo'] = type(exc).__name__
        if isinstance(exc, urllib.error.HTTPError):
            row['http_status'] = exc.code
    row['segundos'] = round(time.perf_counter() - start, 3)
    return row, parsed

def payload(messages, seed=42, max_tokens=2048):
    return {'messages': messages, 'seed': seed, 'temperature': 0,
            'max_tokens': max_tokens, 'stream': False}

def run_contrast(client, private):
    rows = []
    messages = [{'role': 'user', 'content':
        'Devuelve exactamente este JSON y nada mas: {"marca":"PROMPT"}'}]
    for i, seed in enumerate((42, 43), 1):
        expected = 'ESQUEMA_' + str(i)
        body = payload(messages, seed)
        print('Contraste %d/2: control y esquema...' % i, flush=True)
        control, obj = call(client, private, 'control_' + str(i), body)
        control['cumple_prompt'] = obj == {'marca': 'PROMPT'} and control.get('fin') == 'stop'
        rows.append(control)
        body['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'contraste', 'strict': True, 'schema': {
                'type': 'object', 'required': ['marca'], 'additionalProperties': False,
                'properties': {'marca': {'type': 'string', 'enum': [expected]}}}}}
        row, obj = call(client, private, 'esquema_' + str(i), body)
        row['cumple_esquema'] = obj == {'marca': expected} and row.get('fin') == 'stop'
        row['contraste_positivo'] = control['cumple_prompt'] and row['cumple_esquema']
        rows.append(row)
    positive = all(r.get('contraste_positivo') for r in rows if r['prueba'].startswith('esquema'))
    return rows, ('EVIDENCIA_POSITIVA_EN_DOS_CONTRASTES' if positive else 'INCONCLUSO_O_FALLIDO')

def check_batch(obj, n):
    if type(obj) is not dict or set(obj) != {'archivos'}:
        return False
    rows = obj['archivos']
    if type(rows) is not list or len(rows) != n:
        return False
    ids = []
    for r in rows:
        if type(r) is not dict or set(r) != {'id', 'categoria'}:
            return False
        if type(r['id']) is not str or type(r['categoria']) is not str:
            return False
        if r['categoria'] not in CATEGORIES:
            return False
        ids.append(r['id'])
    return sorted(ids) == sorted('f%03d' % i for i in range(n))

def run_batches(client, private):
    rows = []
    texts = ['Apuntes de una asignatura universitaria.',
             'Presupuesto ficticio: ingresos 100 y gastos 40.',
             'Funcion Python para ordenar numeros.', 'Nota sin contexto suficiente.']
    for n in (5, 20, 50):
        print('Lote exploratorio de %d archivos...' % n, flush=True)
        cases = [{'id': 'f%03d' % i, 'contenido': texts[i % 4]} for i in range(n)]
        schema = {'type': 'object', 'required': ['archivos'], 'additionalProperties': False,
            'properties': {'archivos': {'type': 'array', 'minItems': n, 'maxItems': n,
                'items': {'type': 'object', 'required': ['id', 'categoria'],
                    'additionalProperties': False, 'properties': {
                        'id': {'type': 'string', 'enum': [x['id'] for x in cases]},
                        'categoria': {'type': 'string', 'enum': CATEGORIES}}}}}}
        body = payload([{'role': 'system', 'content':
            'Clasifica cada archivo. Usa Revision si no hay contexto. Responde JSON con '
            'archivos: lista de objetos id y categoria. Categorias: ' + ', '.join(CATEGORIES)},
            {'role': 'user', 'content': json.dumps(cases)}], max_tokens=4096)
        body['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'lote', 'strict': True, 'schema': schema}}
        row, obj = call(client, private, 'lote_' + str(n), body)
        row['archivos'] = n
        row['contrato_valido'] = check_batch(obj, n)
        row['completo'] = row['contrato_valido'] and row.get('fin') == 'stop'
        if row['completo']:
            row['aciertos_sobre_n'] = sum(r['categoria'] == CATEGORIES[int(r['id'][1:]) % 4]
                                         for r in obj['archivos'])
        rows.append(row)
        if not row['completo']:
            break  # No ampliar carga tras un fallo ni reintentar silenciosamente.
    return rows

def local_inventory():
    result = {'aislamiento': 'NO_PROBADO', 'imagenes': [], 'motores_activos': []}
    if shutil.which('podman'):
        try:
            p = subprocess.run(['podman', 'images', '--format', 'json'],
                               capture_output=True, text=True, timeout=30)
            images = json.loads(p.stdout) if p.returncode == 0 else []
            result['consulta_imagenes'] = 'OK' if p.returncode == 0 else 'FALLO'
            result['cantidad_imagenes'] = len(images)
            for item in images[:20]:
                ident = item.get('Id', item.get('ID', item.get('id', '')))
                ident = str(ident).removeprefix('sha256:')
                if re.fullmatch('[0-9a-f]{12,64}', ident):
                    result['imagenes'].append({'id_corto': ident[:12]})
        except Exception as exc:
            result['podman_error_tipo'] = type(exc).__name__
    else:
        result['consulta_imagenes'] = 'PODMAN_NO_DISPONIBLE'
    # Solo ejecutables llama-server que ya estén corriendo bajo este usuario.
    # No busca ni ejecuta otros binarios encontrados por el disco.
    seen = set()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            exe = (proc / 'exe').resolve(strict=True)
            if exe.name != 'llama-server' or exe in seen:
                continue
            seen.add(exe)
            p = subprocess.run([str(exe), '--help'], capture_output=True, text=True, timeout=15)
            text = p.stdout + p.stderr
            opts = sorted(set(re.findall(r'--[a-z][a-z0-9-]*', text)))
            opts = [x for x in opts if any(t in x for t in ('reason', 'think', 'jinja', 'chat-template', 'spec-'))]
            v = subprocess.run([str(exe), '--version'], capture_output=True, text=True, timeout=15)
            match = re.search(r'build\s+(\d+).*?commit\s+([a-f0-9]+)', v.stdout + v.stderr)
            result['motores_activos'].append({
                'build': match.group(1) if match else None,
                'commit': match.group(2) if match else None,
                'flags_anunciados': opts,
                'nota': 'Presencia de flags no demuestra su efecto; no se aplicaron cambios.'})
        except (OSError, subprocess.SubprocessError):
            continue
    result['asociacion_motor_puerto'] = 'NO_VERIFICADA'
    return result

def main():
    parser = argparse.ArgumentParser(description='Fase 0: contraste JSON e inventario local. Sin instalaciones.')
    parser.add_argument('--lotes', action='store_true', help='Añadir lotes 5/20/50 solo tras contraste positivo.')
    parser.add_argument('--solo-inventario', action='store_true', help='No enviar solicitudes al modelo.')
    args = parser.parse_args()
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix='ppp_fase0_r2_', dir=Path(__file__).resolve().parent))
    private = root / 'privado'
    private.mkdir(mode=0o700)
    report = {'revision': 2, 'inventario': local_inventory(), 'pruebas': [],
        'limites': ['Contrastes exploratorios: no prueban todos los esquemas ni el mecanismo interno.',
                   'No se midio GPU/RAM; no se certifico aislamiento ni llamadas a herramientas.',
                   'Lotes repetitivos sirven para carga y formato, no para calidad general.',
                   'No se cambio razonamiento, MTP ni configuracion del servidor.',
                   'No compartir carpeta privado; contiene respuestas sin filtrar.']}
    client = Client()
    exit_code = 0
    try:
        if not args.solo_inventario:
            health = client.request('/health')
            if type(health) is not dict or health.get('status') != 'ok':
                raise ValueError('health not ready')
            report['servidor'] = 'LISTO'
            report['pruebas'], report['dictamen_esquema'] = run_contrast(client, private)
            if args.lotes and report['dictamen_esquema'] == 'EVIDENCIA_POSITIVA_EN_DOS_CONTRASTES':
                report['lotes'] = run_batches(client, private)
            elif args.lotes:
                report['lotes'] = 'OMITIDOS_POR_CONTRASTE_NO_POSITIVO'
    except KeyboardInterrupt:
        report['interrumpido'] = True
        exit_code = 130
    except Exception as exc:
        report['error_tipo'] = type(exc).__name__
        exit_code = 1
    write_json(root / 'RESUMEN_COMPARTIBLE_R2.json', report)
    print('\n=== RESUMEN COMPARTIBLE ===')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('\nCarpeta nueva junto a auditar.sh:', root.name)
    print('Compartir: RESUMEN_COMPARTIBLE_R2.json. Conservar privado localmente.')
    return exit_code

if __name__ == '__main__':
    raise SystemExit(main())
