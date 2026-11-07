import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

FLAGS = {'--reasoning', '--reasoning-budget', '--reasoning-effort',
         '--reasoning-format', '--reasoning-preserve', '--no-reasoning-preserve',
         '--chat-template-kwargs', '--jinja'}

def clean(text):
    text = text.replace(str(Path.home()), '<HOME>')
    name = getpass.getuser()
    if len(name) >= 3:
        text = re.sub(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', '<USER>', text)
    text = re.sub(r'https?://\S+', '<URL>', text)
    text = re.sub(r'(?<![\w-])/(?:[^\s,;\)\]\}]+)', '<PATH>', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+', '<EMAIL>', text)
    return text[:5000]

def help_blocks(text):
    blocks = {}
    active = None
    for line in text.splitlines():
        if re.match(r'^\s*-{1,2}[A-Za-z]', line):
            opts = set(re.findall(r'--[a-z][a-z0-9-]*', line))
            matches = opts & FLAGS
            active = sorted(matches)[0] if matches else None
            if active:
                blocks[active] = [line]
        elif active and len(blocks[active]) < 12:
            blocks[active].append(line)
    return {k: clean('\n'.join(v).strip()) for k, v in blocks.items()}

def listener_inodes(text):
    found = set()
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) > 9 and fields[3] == '0A':
            addr, port = fields[1].split(':')
            if port.upper() == '1F90' and addr.upper() == '0100007F':
                found.add(fields[9])
    return found

def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=20)

def engines():
    result = []
    try:
        inodes = listener_inodes(Path('/proc/net/tcp').read_text())
    except OSError:
        inodes = set()
    seen = set()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            exe = (proc / 'exe').resolve(strict=True)
            if exe.name != 'llama-server':
                continue
            associated = False
            for fd in (proc / 'fd').iterdir():
                try:
                    link = os.readlink(fd)
                    if link.startswith('socket:[') and link[8:-1] in inodes:
                        associated = True
                except OSError:
                    pass
            # Record per executable and association; do not expose PIDs or paths.
            key = (str(exe), associated)
            if key in seen:
                continue
            seen.add(key)
            h = run([str(exe), '--help'])
            v = run([str(exe), '--version'])
            match = re.search(r'build\s+(\d+).*?commit\s+([a-f0-9]+)', v.stdout + v.stderr)
            result.append({'build': match.group(1) if match else None,
                'commit': match.group(2) if match else None,
                'asociado_127_0_0_1_8080': associated,
                'ayuda_exit_code': h.returncode,
                'ayuda_seleccionada': help_blocks(h.stdout + '\n' + h.stderr)})
        except (OSError, subprocess.SubprocessError):
            continue
    return result

def safe_image(item):
    config = item.get('Config') or {}
    cmd = config.get('Cmd') or []
    ep = config.get('Entrypoint') or []
    words = (cmd if isinstance(cmd, list) else []) + (ep if isinstance(ep, list) else [])
    # Metadata is not proof that an interpreter exists. Never execute images.
    known = sorted({Path(x).name for x in words if isinstance(x, str)
                    and Path(x).name in ('python', 'python3', 'sh', 'bash')})
    arch = item.get('Architecture')
    system = item.get('Os')
    return {'arquitectura': arch if arch in ('arm64', 'amd64', 'arm', '386') else 'otra_o_desconocida',
            'sistema': system if system in ('linux', 'windows') else 'otro_o_desconocido',
            'interpretes_mencionados_en_config': known,
            'interpretes_comprobados': False,
            'volumenes_declarados': len(config.get('Volumes') or {}),
            'ejecutada': False}

def images():
    if not shutil.which('podman'):
        return {'estado': 'NO_DISPONIBLE'}
    try:
        p = run(['podman', 'images', '--format', 'json'])
        if p.returncode:
            return {'estado': 'CONSULTA_FALLIDA'}
        ids = set()
        for item in json.loads(p.stdout):
            ident = str(item.get('Id', item.get('ID', item.get('id', '')))).removeprefix('sha256:')
            if re.fullmatch('[a-f0-9]{12,64}', ident):
                ids.add(ident)
        rows = []
        for ident in sorted(ids)[:30]:
            p = run(['podman', 'image', 'inspect', ident])
            if p.returncode:
                rows.append({'id_corto': ident[:12], 'estado': 'INSPECCION_FALLIDA'})
                continue
            data = json.loads(p.stdout)
            row = safe_image(data[0])
            row['id_corto'] = ident[:12]
            rows.append(row)
        return {'estado': 'OK', 'cantidad_unica': len(ids), 'imagenes': rows}
    except (OSError, ValueError, TypeError, IndexError, subprocess.SubprocessError) as exc:
        return {'estado': 'FALLO', 'error_tipo': type(exc).__name__}

def main():
    argparse.ArgumentParser(description='Inspeccion R3 sin inferencia, descargas ni contenedores.').parse_args()
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix='ppp_fase0_r3_', dir=Path(__file__).resolve().parent))
    print('Consultando ayuda del motor y metadatos locales...', flush=True)
    report = {'revision': 3, 'motores': engines(), 'podman': images(),
              'aislamiento': 'NO_PROBADO', 'razonamiento_modificado': False,
              'limites': ['Asociacion por socket IPv4 observado; una ausencia no demuestra que no exista servidor.',
                         'Ayuda filtrada; revisar el resumen antes de compartirlo.',
                         'Metadatos de imagen no prueban presencia de Python ni procedencia confiable.',
                         'No se han iniciado contenedores ni solicitudes de inferencia.']}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    with (root / 'RESUMEN_COMPARTIBLE_R3.json').open('x', encoding='utf-8') as f:
        f.write(text)
    print(text)
    print('Carpeta nueva junto al script:', root.name)
    print('Compartir RESUMEN_COMPARTIBLE_R3.json tras revisar el contenido.')

if __name__ == '__main__':
    main()
