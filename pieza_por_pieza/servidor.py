"""Gestión local de llama-server sin tmux ni terminal adicional."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen

HOST='127.0.0.1'
PORT=8080

class Gestor:
    def __init__(self):
        self.proceso=None
        self.registro=None
        self.ruta_registro=None
        self.vision=False

    def puerto_ocupado(self):
        with socket.socket() as sock:
            sock.settimeout(0.3)
            return sock.connect_ex((HOST, PORT)) == 0

    def listo(self):
        try:
            with urlopen(f'http://{HOST}:{PORT}/v1/models', timeout=1) as response:
                return response.status == 200
        except (OSError, ValueError):
            return False

    def iniciar(self, ejecutable, modelo, ctx=8192, gpu=0, parallel=1, reasoning=False, mmproj=None, **_):
        if self.proceso and self.proceso.poll() is None:
            raise RuntimeError('Ya hay un servidor administrado por esta sesión.')
        if self.puerto_ocupado():
            raise RuntimeError('El puerto 8080 está ocupado. No se detendrá ningún proceso ajeno.')
        if not Path(ejecutable).is_file() or (os.name!='nt' and not os.access(ejecutable,os.X_OK)):
            raise ValueError('llama-server no es ejecutable.')
        if Path(modelo).suffix.lower()!='.gguf' or not Path(modelo).is_file():
            raise ValueError('Modelo GGUF no disponible.')
        if ctx<512 or gpu<0 or parallel<1:
            raise ValueError('Parámetros fuera de rango.')
        cmd=[str(ejecutable),'--model',str(modelo),'--host',HOST,'--port',str(PORT),
             '--ctx-size',str(ctx),'--n-gpu-layers',str(gpu),'--parallel',str(parallel)]
        if reasoning:
            cmd+=['--reasoning','off']
        if mmproj:
            if Path(mmproj).suffix.lower()!='.gguf' or not Path(mmproj).is_file():
                raise ValueError('Archivo mmproj no disponible.')
            cmd+=['--mmproj',str(mmproj)]  # visión: Qwen puede mirar imágenes
        self.vision=bool(mmproj)
        # Registro privado, fuera del repositorio; no se canaliza stderr a PIPE.
        fd, nombre=tempfile.mkstemp(prefix='ppp_llama_',suffix='.log')
        try:os.fchmod(fd,0o600)
        except (AttributeError,OSError):pass  # Windows antiguo: el archivo temporal ya es privado del usuario.
        self.ruta_registro=Path(nombre)
        self.registro=os.fdopen(fd,'w',encoding='utf-8')
        # Grupo de procesos propio: Ctrl+C en el menú no mata al servidor a medias; NEXORA lo cierra ordenadamente.
        extra={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
        try:
            self.proceso=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=self.registro,
                                          stderr=subprocess.STDOUT,**extra)
        except Exception:
            self.registro.close();self.registro=None
            raise
        return self.proceso.pid

    def estado(self):
        if self.proceso is not None:
            code=self.proceso.poll()
            if code is not None:
                return f'Proceso terminado (código {code})'
            return 'Listo' if self.listo() else 'Cargando modelo / iniciando'
        return 'Servidor externo activo (no administrado)' if self.puerto_ocupado() else 'Detenido'

    def ultimas_lineas(self, n=12):
        if not self.ruta_registro or not self.ruta_registro.is_file():
            return 'No hay registro disponible.'
        with self.ruta_registro.open('r',encoding='utf-8',errors='replace') as f:
            from collections import deque
            return ''.join(deque(f,maxlen=n))

    def detener(self):
        p=self.proceso
        if p is None:
            return False
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=5)
        self.proceso=None
        if self.registro:
            self.registro.close();self.registro=None
        return True
