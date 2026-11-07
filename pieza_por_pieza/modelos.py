#!/usr/bin/env python3
"""Pieza por Pieza: selector local interactivo. No descarga ni mueve modelos."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from urllib.request import urlopen

HOST, PORT = '127.0.0.1', 8080
SKIP_NAMES = ('ggml-vocab-', 'mmproj-', 'stories260k', 'tokenizer', 'vocab-')
SKIP_PARTS = ('/llama.cpp/models/', '/llama.cpp/tests/', '/llama.cpp/examples/')


def ask(prompt, default=''):
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt from None
    return answer if answer else default


def active_models():
    try:
        with urlopen(f'http://{HOST}:{PORT}/v1/models', timeout=2) as response:
            data = json.load(response)
        return [v.get('id', 'desconocido') for v in data.get('data', [])]
    except (OSError, ValueError, TypeError):
        return []


def unique_paths(paths):
    seen, result = set(), []
    for path in paths:
        p = Path(path).expanduser()
        try:
            if not p.is_dir():
                continue
            key = str(p.resolve())
        except OSError:
            continue
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


def standard_roots():
    h = Path.home()
    return unique_paths([h/'models', h/'modelos', h/'Documents'/'modelos',
                         h/'.cache'/'huggingface'/'hub', h/'pieza-por-pieza',
                         h/'Downloads'/'lab', h/'Downloads',
                         h/'.lmstudio'/'models', h/'.cache'/'lm-studio'/'models',   # LM Studio (todos los sistemas)
                         h/'AppData'/'Local'/'llama.cpp',                        # Windows
                         h/'Library'/'Caches'/'llama.cpp'])                      # macOS


def mounts():
    found = []
    if os.name == 'nt':  # Windows: unidades C:, D:, E:...
        import string
        return unique_paths([Path(f'{d}:/') for d in string.ascii_uppercase if Path(f'{d}:/').exists()])
    for base in ('/media', '/mnt', '/run/media', '/Volumes'):  # Linux y macOS
        p = Path(base)
        if not p.is_dir():
            continue
        try:
            first = list(p.iterdir())[:40]
            for child in first:
                if child.is_dir() and not child.is_symlink():
                    found.append(child)
                    try:
                        for grandchild in list(child.iterdir())[:40]:
                            if grandchild.is_dir() and not grandchild.is_symlink():
                                found.append(grandchild)
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
    return unique_paths(found)


def scan(roots, max_depth=14, max_entries=250000):
    found, visited, limited = {}, 0, False
    for root in unique_paths(roots):
        for current, dirs, files in os.walk(root, followlinks=False):
            depth = len(Path(current).relative_to(root).parts)
            dirs[:] = sorted(d for d in dirs if not d.startswith('.') and not (Path(current)/d).is_symlink()) if depth < max_depth else []
            for name in files:
                visited += 1
                if visited > max_entries:
                    limited = True
                    break
                if not name.lower().endswith('.gguf'):
                    continue
                p = Path(current)/name
                try:
                    if p.is_file():
                        found[str(p.resolve())] = p  # accept symlinks; avoid duplicates
                except OSError:
                    pass
            if limited:
                break
        if limited:
            break
    return sorted(found.values(), key=lambda p: p.name.casefold()), limited


def category(p):
    name = p.name.lower()
    s = str(p).lower()
    if name.startswith(SKIP_NAMES) or any(part in s for part in SKIP_PARTS):
        return 'auxiliar'
    if re.search(r'-\d{5}-of-\d{5}\.gguf$', name):
        return 'fragmento'
    if any(k in name for k in ('flux', 'wan2', 'qwen-image', 'diffusion', 'demucs')):
        return 'especializado'
    if any(k in name for k in ('bge-', 'embed', 'rerank')):
        return 'especializado'
    return 'general'


def pretty_size(p):
    try:
        n = p.stat().st_size
        return f'{n / 1024**3:.2f} GiB' if n >= 1024**3 else f'{n / 1024**2:.1f} MiB'
    except OSError:
        return 'tamaño desconocido'


def choose_model(models):
    general = [p for p in models if category(p) == 'general']
    visible = general
    while True:
        print('\nModelos principales encontrados:', len(general), '| otros archivos:', len(models)-len(general))
        for i, p in enumerate(visible, 1):
            print(f'  {i}. {p.name} ({pretty_size(p)})')
        print('  T. Mostrar todos los GGUF')
        print('  R. Escribir la ruta de un GGUF')
        print('  0. Volver')
        choice = ask('Elegí una opción: ').lower()
        if choice == '0':
            return None
        if choice == 't':
            visible = models
            continue
        if choice == 'r':
            raw = ask('Ruta del archivo .gguf: ').strip('"\'')
            p = Path(raw).expanduser()
        elif choice.isdigit() and 1 <= int(choice) <= len(visible):
            p = visible[int(choice)-1]
        else:
            print('Opción no reconocida.')
            continue
        if p.suffix.lower() == '.gguf' and p.is_file():
            if category(p) != 'general':
                print('AVISO: archivo auxiliar, fragmento o modelo especializado; puede requerir otro programa o más archivos.')
                if ask('¿Continuar de todos modos? [s/N]: ').lower() not in ('s','si','sí'):
                    continue
            return p
        print('No se encontró un archivo GGUF válido.')


def choose_server():
    h = Path.home()
    candidates = [Path(p) for p in (shutil.which('llama-server'),) if p]
    exe = 'llama-server.exe' if os.name == 'nt' else 'llama-server'
    for base in (h/'pieza-por-pieza'/'laboratorio'/'llama.cpp', h/'llama.cpp'):
        candidates += [base/'build'/'bin'/exe, base/'build'/'bin'/'Release'/exe]  # Release: Visual Studio
    candidates += [Path('/opt/homebrew/bin/llama-server'), Path('/usr/local/bin/llama-server')]  # Homebrew
    candidates = [p for p in candidates if p.is_file() and (os.name == 'nt' or os.access(p, os.X_OK))]
    candidates = list(dict.fromkeys(map(str, candidates)))
    while True:
        print('\nEjecutables llama-server:')
        for i, p in enumerate(candidates, 1):
            print(f'  {i}. {p}')
        print('  R. Indicar otra ubicación')
        print('  0. Cancelar')
        value = ask('Elegí una opción: ', '1' if len(candidates)==1 else '').lower()
        if value == '0':
            return None
        if value == 'r':
            p = Path(ask('Ruta de llama-server: ').strip('"\'')).expanduser()
        elif value.isdigit() and 1 <= int(value) <= len(candidates):
            p = Path(candidates[int(value)-1])
        else:
            print('Opción no válida.')
            continue
        if p.is_file() and (os.name == 'nt' or os.access(p, os.X_OK)):
            return p
        print('No se encontró un ejecutable accesible.')


def folder_dialog():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(title='Elegí dónde buscar modelos GGUF')
        root.destroy()
        return Path(selected) if selected else None
    except Exception:
        return None


def pick_folders():
    print('\nElegir carpeta:')
    print('  1. Abrir selector gráfico de carpetas (si está disponible)')
    print('  2. Elegir una unidad o carpeta montada')
    print('  3. Escribir una ruta')
    print('  0. Volver')
    choice = ask('Opción: ')
    if choice == '1':
        p = folder_dialog()
        if not p:
            print('No se pudo abrir el selector o se canceló. Usá otra opción.')
            return []
        return unique_paths([p])
    if choice == '2':
        choices = mounts()
        if not choices:
            print('No se encontraron unidades montadas accesibles.')
            return []
        for i, p in enumerate(choices, 1):
            print(f'  {i}. {p}')
        n = ask('Número (Enter para volver): ')
        if n.isdigit() and 1 <= int(n) <= len(choices):
            return [choices[int(n)-1]]
        return []
    if choice == '3':
        p = Path(ask('Carpeta: ').strip('"\'')).expanduser()
        if p.is_dir():
            return [p]
        print('Esa carpeta no existe o no es accesible.')
    return []


def settings_menu(settings):
    while True:
        print(f'\nConfiguración: contexto={settings["ctx"]}, capas GPU={settings["gpu"]}, paralelo={settings["parallel"]}, reasoning off={settings["reasoning"]}'
              + (f', modo grabación={settings["grabacion"]}' if 'grabacion' in settings else ''))
        print('  1. Contexto | 2. Capas GPU | 3. Paralelismo | 4. Alternar reasoning off'
              + (' | 5. Alternar modo grabación' if 'grabacion' in settings else '') + ' | 0. Volver')
        choice = ask('Opción: ')
        if choice == '0':
            return
        if choice == '4':
            settings['reasoning'] = not settings['reasoning']
        elif choice == '5' and 'grabacion' in settings:
            settings['grabacion'] = not settings['grabacion']
            print('Modo grabación ' + ('ACTIVADO: se ocultan tu carpeta personal y tu usuario.' if settings['grabacion'] else 'desactivado.'))
        elif choice in ('1','2','3'):
            key = {'1':'ctx','2':'gpu','3':'parallel'}[choice]
            value = ask('Nuevo valor entero: ')
            if value.isdigit() and int(value) >= (512 if key=='ctx' else 1 if key=='parallel' else 0):
                settings[key] = int(value)
            else:
                print('Valor inválido.')


def run(model, settings):
    if category(model) != 'general':
        print('No se inicia automáticamente un modelo especializado o fragmentado.')
        return
    server = choose_server()
    if server is None:
        return
    cmd = [str(server), '--model', str(model), '--host', HOST, '--port', str(PORT),
           '--ctx-size', str(settings['ctx']), '--n-gpu-layers', str(settings['gpu']),
           '--parallel', str(settings['parallel'])]
    if settings['reasoning']:
        cmd += ['--reasoning','off']
    print(f'\nModelo: {model.name} ({pretty_size(model)})')
    print(f'Ejecutable: {server.name}')
    print(f'Contexto: {settings["ctx"]}; GPU: {settings["gpu"]}; paralelo: {settings["parallel"]}; reasoning off: {settings["reasoning"]}')
    print('No se descargará ni moverá ningún archivo.')
    if ask('¿Iniciar en 127.0.0.1:8080? [s/N]: ').lower() not in ('s','si','sí'):
        print('Cancelado.')
        return
    if active_models():
        print('Ya existe un servidor compatible. No se iniciará otro.')
        return
    with socket.socket() as sock:
        if sock.connect_ex((HOST,PORT)) == 0:
            print('El puerto 8080 está ocupado. No se iniciará otro servidor.')
            return
    print('Iniciando servidor. Ctrl+C para detenerlo.')
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        print('\nDetenido.')


def main():
    parser = argparse.ArgumentParser(description='Selector interactivo de modelos GGUF locales')
    parser.add_argument('--buscar-en', action='append', default=[])
    parser.add_argument('--gpu-layers', type=int, default=0)
    parser.add_argument('--ctx', type=int, default=8192)
    parser.add_argument('--parallel', type=int, default=1)
    parser.add_argument('--reasoning-off', action='store_true')
    args = parser.parse_args()
    settings = {'gpu':args.gpu_layers,'ctx':args.ctx,'parallel':args.parallel,'reasoning':args.reasoning_off}
    if settings['gpu'] < 0 or settings['ctx'] < 512 or settings['parallel'] < 1:
        parser.error('Parámetros fuera de rango')
    print('PIEZA POR PIEZA — ASISTENTE LOCAL V3')
    if active_models():
        print('Ya hay un servidor compatible en 127.0.0.1:8080. No se modificará.')
        return
    while True:
        print('\n¿Qué querés hacer?')
        print('  1. Buscar modelos en carpetas habituales')
        print('  2. Elegir dónde buscar (ventana, unidades montadas o ruta)')
        print('  3. Elegir un archivo GGUF directamente')
        print('  4. Configuración avanzada')
        print('  0. Salir')
        choice = ask('Opción: ')
        if choice == '0':
            return
        if choice == '4':
            settings_menu(settings)
            continue
        if choice == '3':
            model = choose_model([])
        elif choice in ('1','2'):
            folders = standard_roots() + [Path(p).expanduser() for p in args.buscar_en] if choice=='1' else pick_folders()
            if not folders:
                continue
            print('Buscando archivos GGUF (puede tardar según el tamaño de la carpeta)...')
            models, limited = scan(folders)
            if limited:
                print('AVISO: se alcanzó el límite de archivos; los resultados pueden estar incompletos. Elegí una carpeta más específica.')
            model = choose_model(models)
        else:
            print('Opción no reconocida.')
            continue
        if model:
            run(model, settings)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelado.')
    except OSError as exc:
        print('Error del sistema:', exc, file=sys.stderr)
        sys.exit(2)
