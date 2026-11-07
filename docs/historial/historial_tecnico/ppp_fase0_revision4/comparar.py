import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import sondas as s

BASE = Path(__file__).resolve().parent
ALLOWED = {'--model','-m','--host','--port','--ctx-size','-c','--n-gpu-layers','-ngl',
           '--parallel','-np','--reasoning','-rea','--spec-type','--alias',
           '--flash-attn','-fa','--threads','-t','--threads-batch','-tb'}
SWITCHES = {'--jinja','--no-jinja'}
ENV_KEYS = {'CUDA_VISIBLE_DEVICES','LD_LIBRARY_PATH','LD_PRELOAD','PATH',
            'GGML_CUDA_ENABLE_UNIFIED_MEMORY','CUDA_MODULE_LOADING'}

class CheckError(Exception):
    pass

def parse_args(argv):
    found = {}
    i = 1
    while i < len(argv):
        flag = argv[i]
        if flag in SWITCHES:
            found[flag] = True
            i += 1
        elif flag in ALLOWED and i + 1 < len(argv):
            if flag in found:
                raise CheckError('ARGUMENTO_REPETIDO')
            found[flag] = argv[i+1]
            i += 2
        else:
            raise CheckError('CONFIGURACION_NO_CUBIERTA_POR_ESTA_PRUEBA')
    return found

def off_argv(argv):
    parse_args(argv)
    result = [argv[0]]
    i = 1
    while i < len(argv):
        flag = argv[i]
        width = 1 if flag in SWITCHES else 2
        if flag not in ('--reasoning','-rea'):
            result.extend(argv[i:i+width])
        i += width
    return result + ['--reasoning','off']

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()

def listeners():
    ids = set()
    try:
        for line in Path('/proc/net/tcp').read_text().splitlines()[1:]:
            f = line.split()
            if len(f) > 9 and f[1] == '0100007F:1F90' and f[3] == '0A':
                ids.add(f[9])
    except OSError:
        pass
    return ids

def owns(proc, ids):
    try:
        for fd in (proc/'fd').iterdir():
            try:
                if os.readlink(fd) in {'socket:['+i+']' for i in ids}:
                    return True
            except OSError:
                pass
    except OSError:
        pass
    return False

def snapshot():
    candidates = []
    ids = listeners()
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid() or not owns(proc, ids):
                continue
            exe = (proc/'exe').resolve(strict=True)
            if exe.name != 'llama-server':
                continue
            argv = [os.fsdecode(x) for x in (proc/'cmdline').read_bytes().split(b'\0') if x]
            argv[0] = str(exe)
            flags = parse_args(argv)
            if flags.get('--host') != '127.0.0.1' or flags.get('--port', '8080') != '8080':
                raise CheckError('HOST_O_PUERTO_NO_COMPATIBLE')
            model = flags.get('--model', flags.get('-m'))
            cwd = str((proc/'cwd').resolve(strict=True))
            if not model or not (Path(cwd)/model).is_file():
                raise CheckError('MODELO_LOCAL_NO_VERIFICABLE')
            if flags.get('--reasoning', flags.get('-rea', 'auto')) == 'off':
                raise CheckError('LINEA_BASE_YA_TIENE_REASONING_OFF')
            if flags.get('--spec-type','none') != 'none':
                raise CheckError('MTP_O_ESPECULACION_ACTIVA')
            env = {}
            for item in (proc/'environ').read_bytes().split(b'\0'):
                if b'=' not in item:
                    continue
                k, v = item.split(b'=',1)
                key = os.fsdecode(k)
                if key.startswith('LLAMA_'):
                    raise CheckError('CONFIGURACION_LLAMA_EN_ENTORNO_REQUIERE_REVISION')
                if key in ENV_KEYS:
                    env[key] = os.fsdecode(v)
            version = subprocess.run([str(exe),'--version'], capture_output=True, text=True, timeout=20)
            if not re.search(r'build\s+12052.*commit\s+84d9ce0fa', version.stdout+version.stderr):
                raise CheckError('BUILD_NO_ESPERADA')
            candidates.append({'version': 1, 'argv': argv, 'cwd': cwd, 'env': env,
                               'engine_sha256': digest(exe)})
        except (OSError, subprocess.SubprocessError):
            continue
    if len(candidates) != 1:
        raise CheckError('NO_SE_IDENTIFICO_UN_SOLO_LLAMA_SERVER_EN_8080')
    return candidates[0]

def port_free():
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1',8080))
            return True
        except OSError:
            return False

def read_state(root):
    state = json.loads((root/'privado/config_original.json').read_text())
    if state.get('version') != 1:
        raise CheckError('VERSION_DE_ESTADO_NO_ADMITIDA')
    parse_args(state['argv'])
    if digest(state['argv'][0]) != state['engine_sha256']:
        raise CheckError('EL_BINARIO_CAMBIO_DESDE_LA_LINEA_BASE')
    return state

def child_env(state):
    env = dict(os.environ)
    for key in list(env):
        if key.startswith('LLAMA_') or key in ENV_KEYS:
            env.pop(key)
    env.update(state['env'])
    return env

def stop_child(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)

def wait_ready(proc):
    client = s.Client()
    deadline = time.monotonic()+240
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise CheckError('EL_SERVIDOR_DE_PRUEBA_TERMINO_AL_ARRANCAR')
        # Solo consultar health después de asociar el puerto al hijo propio.
        if owns(Path('/proc')/str(proc.pid), listeners()):
            try:
                if client.request('/health').get('status') == 'ok':
                    return
            except Exception:
                pass
        time.sleep(1)
    raise CheckError('ARRANQUE_NO_COMPLETADO_A_TIEMPO')

def measurements(root, mode):
    folder = root/'privado'/mode
    folder.mkdir(mode=0o700)
    rows = s.run_batches(s.Client(), folder)
    for row in rows:
        req = folder/(row['prueba']+'_solicitud.json')
        row['solicitud_sha256'] = digest(req)
    s.write_json(root/(mode+'.json'), rows)
    return rows

def public_report(root):
    report = {'revision': 4, 'cambio_solicitado': '--reasoning off',
              'build_objetivo': '12052 / 84d9ce0fa', 'comparaciones': [],
              'limites': ['Prueba exploratoria de una corrida por condicion; no benchmark definitivo.',
                         'Comparacion ordenada actual/off; caches y calentamiento pueden afectar tiempos.',
                         'No se midieron RAM/GPU ni integridad completa del modelo.',
                         'Ausencia de reasoning_content no demuestra ausencia de todo computo interno.',
                         'No se ejecuto ni certifico aislamiento Podman.']}
    data = {}
    for mode in ('actual','off'):
        p = root/(mode+'.json')
        if p.exists():
            data[mode] = json.loads(p.read_text())
            report[mode] = data[mode]
    left = {r['archivos']: r for r in data.get('actual',[])}
    for right in data.get('off',[]):
        old = left.get(right['archivos'])
        if old:
            row = {'archivos':right['archivos'], 'solicitudes_identicas':
                   old.get('solicitud_sha256') == right.get('solicitud_sha256'),
                   'ambos_completos': old.get('completo',False) and right.get('completo',False)}
            if row['solicitudes_identicas'] and row['ambos_completos'] and right['segundos'] > 0:
                row['factor_tiempo_actual_sobre_off'] = round(old['segundos']/right['segundos'],3)
            report['comparaciones'].append(row)
    error_file = root/'ultimo_error.json'
    if error_file.exists():
        report['ultimo_error_registrado'] = json.loads(error_file.read_text())
    # Se reemplaza solo el resumen propio de esta sesión.
    (root/'RESUMEN_COMPARTIBLE_R4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report

def find_session(name):
    candidates = [BASE/name] if name else sorted(BASE.glob('ppp_fase0_r4_*'))
    candidates = [p for p in candidates if p.is_dir() and p.parent.resolve()==BASE
                  and not p.is_symlink() and p.name.startswith('ppp_fase0_r4_')]
    if len(candidates)!=1:
        raise CheckError('INDICAR_UNA_SESION_CON_--sesion_NOMBRE_DE_CARPETA')
    return candidates[0]

def main():
    parser = argparse.ArgumentParser(description='Comparacion actual/off; nunca detiene un servidor preexistente.')
    parser.add_argument('modo', choices=('base','off','restaurar'))
    parser.add_argument('--sesion', help='Nombre de la carpeta creada en base, si hay varias.')
    args = parser.parse_args()
    os.umask(0o077)
    root = None
    try:
        if args.modo == 'base':
            state = snapshot()
            if s.Client().request('/health').get('status') != 'ok':
                raise CheckError('SERVIDOR_NO_LISTO')
            root = Path(tempfile.mkdtemp(prefix='ppp_fase0_r4_',dir=BASE))
            (root/'privado').mkdir(mode=0o700)
            s.write_json(root/'privado/config_original.json',state)
            measurements(root,'actual')
            print('Base guardada. Ahora detener TU servidor con Ctrl+C y ejecutar: bash comparar.sh off')
        else:
            root = find_session(args.sesion)
            state = read_state(root)
            if args.modo == 'off':
                baseline = json.loads((root/'actual.json').read_text())
                if len(baseline) != 3 or not all(r.get('completo') for r in baseline):
                    raise CheckError('LINEA_BASE_INCOMPLETA_REVISAR_ANTES_DE_OFF')
            if not port_free():
                raise CheckError('8080_OCUPADO_DETENER_MANUALMENTE_EL_SERVIDOR_ANTES')
            if args.modo=='off' and ((root/'off.json').exists() or (root/'privado/off').exists()):
                raise CheckError('PRUEBA_OFF_YA_EXISTE_NO_SE_SOBRESCRIBE')
            argv = off_argv(state['argv']) if args.modo=='off' else state['argv']
            log_path=root/'privado'/('arranque_'+args.modo+'_'+str(time.time_ns())+'.log')
            with log_path.open('x') as log:
                print('Iniciando servidor local; registro privado. No se carga una segunda copia si 8080 esta ocupado.',flush=True)
                proc = subprocess.Popen(argv,cwd=state['cwd'],env=child_env(state),stdout=log,stderr=log)
                try:
                    wait_ready(proc)
                    if args.modo=='off':
                        measurements(root,'off')
                    else:
                        print('Servidor original restaurado. Dejar esta terminal abierta; Ctrl+C para detenerlo.',flush=True)
                        while proc.poll() is None:
                            time.sleep(1)
                finally:
                    stop_child(proc)
            if args.modo=='off':
                print('Servidor de prueba detenido. Restaurar con: bash comparar.sh restaurar')
        return 0
    except KeyboardInterrupt:
        print('Interrumpido. Se conserva la evidencia ya escrita; revisar privado antes de repetir.')
        return 130
    except Exception as exc:
        error = str(exc) if isinstance(exc,CheckError) else type(exc).__name__
        if root is not None:
            (root/'ultimo_error.json').write_text(json.dumps({'modo':args.modo,'error':error}))
        print('No se completo:', error)
        print('No se detuvieron procesos preexistentes.')
        return 1
    finally:
        if root is not None:
            public_report(root)
            print('Sesion:',root.name)
            print('Compartir RESUMEN_COMPARTIBLE_R4.json; no compartir privado/.')

if __name__=='__main__':
    raise SystemExit(main())
