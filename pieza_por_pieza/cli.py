"""Interfaz integrada de laboratorio. Solo ejecuta movimientos en laboratorio R5-R sintético."""
from pathlib import Path
import os
import subprocess
import sys
from . import modelos
from .servidor import Gestor
from . import r5r

manager=Gestor()
DEFAULTS={'ctx':8192,'gpu':0,'parallel':1,'reasoning':False,'grabacion':False,'ultimo_modelo':'','ultimo_servidor':''}
CONFIG=Path.home()/'.config'/'nexora'/'config.json'

def cargar_config():
    """Recupera la configuración guardada; ante cualquier problema usa los valores por defecto."""
    data=dict(DEFAULTS)
    try:
        import json
        saved=json.loads(CONFIG.read_text(encoding='utf-8'))
        for k,v in DEFAULTS.items():
            if type(saved.get(k)) is type(v):data[k]=saved[k]
    except (OSError,ValueError,AttributeError):pass
    return data

def guardar_config():
    import json
    try:
        CONFIG.parent.mkdir(parents=True,exist_ok=True)
        CONFIG.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
    except OSError as e:print('No se pudo guardar la configuración:',e)

settings=cargar_config()

class _Grabacion:
    """Modo grabación: oculta tu carpeta personal y tu usuario en todo lo que NEXORA imprime."""
    def __init__(self, real):
        import getpass, re
        self.real=real
        home=str(Path.home())
        try:usuario=getpass.getuser()
        except Exception:usuario=Path.home().name
        self.cambios=[(home,'~')]
        self.patron=re.compile(r'(?<=[/\\])'+re.escape(usuario)+r'(?=[/\\]|$)') if len(usuario)>=2 else None
    def write(self, texto):
        for a,b in self.cambios:texto=texto.replace(a,b)
        if self.patron:texto=self.patron.sub('usuario',texto)
        return self.real.write(texto)
    def __getattr__(self, nombre):return getattr(self.real,nombre)

def _activar_grabacion():
    import sys
    if (settings.get('grabacion') or os.environ.get('NEXORA_GRABACION')=='1') and not isinstance(sys.stdout,_Grabacion):
        sys.stdout=_Grabacion(sys.stdout)

def _correr(args):
    """Ejecuta un paso auxiliar mostrando su salida por el mismo filtro (modo grabación)."""
    r=subprocess.run(args,check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    print(r.stdout,end='')

def buscar_modelo():
    while True:
        print('\n1. Buscar en carpetas habituales  2. Elegir carpeta  3. Pegar ruta GGUF  0. Volver')
        op=modelos.ask('Opción: ')
        if op=='0':return None
        if op.strip('"\'').lower().endswith('.gguf'):  # pegaron la ruta directamente en el menú
            from pathlib import Path as _P
            p=_P(op.strip('"\'')).expanduser()
            if p.is_file():return p
            print('No se encontró ese archivo GGUF.');continue
        if op=='1': roots=modelos.standard_roots()
        elif op=='2': roots=modelos.pick_folders()
        elif op=='3':
            from pathlib import Path as _P
            p=_P(modelos.ask('Ruta del archivo .gguf: ').strip('"\'')).expanduser()
            if p.suffix.lower()=='.gguf' and p.is_file():return p
            print('No se encontró un archivo GGUF válido en esa ruta.');continue
        else:continue
        if not roots:continue
        print('Buscando GGUF...')
        items,limited=modelos.scan(roots)
        if limited:print('Aviso: búsqueda incompleta por límite; elegí una carpeta más específica.')
        selected=modelos.choose_model(items)
        if selected:return selected

def configurar_servidor():
    if manager.proceso and manager.proceso.poll() is None:
        print('Ya hay un servidor iniciado por esta sesión.');return
    if manager.puerto_ocupado():
        print('Puerto 8080 ocupado; no se iniciará otro servidor.');return
    ultimo=Path(settings.get('ultimo_modelo') or '/nada');srv=Path(settings.get('ultimo_servidor') or '/nada')
    model=server=None
    if ultimo.is_file() and srv.is_file():
        print(f'\nÚltimo modelo usado: {ultimo.name}')
        if modelos.ask('¿Usarlo de nuevo? [S/n]: ').lower() not in ('n','no'):model,server=ultimo,srv
    if model is None:
        model=buscar_modelo()
        if not model:return
        if modelos.category(model)!='general':
            print('Este archivo parece auxiliar, fragmentado o especializado; no se inicia desde este menú.');return
        server=modelos.choose_server()
        if server is None:return
    print(f'\nModelo: {model.name} ({modelos.pretty_size(model)})')
    print(f'Contexto={settings["ctx"]}, GPU={settings["gpu"]}, paralelo={settings["parallel"]}, reasoning off={settings["reasoning"]}')
    mmproj=None
    candidatos=sorted(model.parent.glob('mmproj*.gguf'))
    if candidatos:
        print(f'Visión disponible: {candidatos[0].name} (permite que Qwen mire fotos).')
        if modelos.ask('¿Activar visión? [S/n]: ').lower() not in ('n','no'):mmproj=candidatos[0]
    else:
        print('Sin archivo mmproj junto al modelo: Qwen solo leerá texto (criterio 7 no disponible).')
    print('No se descargan modelos ni se modifican documentos.')
    if modelos.ask('¿Iniciar servidor local en segundo plano? [s/N]: ').lower() not in ('s','si','sí'):return
    opciones={k:settings[k] for k in ('ctx','gpu','parallel','reasoning')}
    pid=manager.iniciar(server,model,mmproj=mmproj,**opciones)
    settings['ultimo_modelo'],settings['ultimo_servidor']=str(model),str(server);guardar_config()
    print(f'Proceso iniciado (PID {pid}). Estado: {manager.estado()}')
    print('Volvé a consultar el estado; la carga del modelo puede tardar.')

def laboratorio():
    print('\nR5-R: SOLO DEMOSTRACIÓN CON 30 ARCHIVOS SINTÉTICOS.')
    print('La clasificación de IA y el ejecutor NO están conectados automáticamente.')
    root=Path.cwd()/'demo_r5r'
    print('Carpeta de demostración:',root)
    while True:
        print('\n1. Preparar  2. Planificar  3. Verificar  4. Aprobar  5. Ejecutar  6. Revertir  0. Volver')
        op=modelos.ask('Opción: ')
        names={'1':'prepare','2':'plan','3':'verify','4':'approve','5':'execute','6':'rollback'}
        if op=='0':return
        if op not in names:continue
        cmd=names[op]
        args=[sys.executable,str(Path(r5r.__file__).resolve()),cmd,'--root',str(root)]
        if cmd=='approve':
            if not (root/'state'/'plan.json').is_file():
                print('Primero generá el plan.');continue
            import json
            digest=json.loads((root/'state'/'plan.json').read_text())['plan_sha256']
            print('Digest del plan:',digest)
            phrase=modelos.ask('Escribí exactamente AUTORIZO DEMO R5R: ')
            args+=['--digest',digest,'--confirm',phrase]
        if cmd in ('execute','rollback'):
            if modelos.ask(f'Confirmá {cmd} de archivos sintéticos [s/N]: ').lower() not in ('s','si','sí'):continue
        _correr(args)

def auditoria_copias():
    """Auditar CSV local y ensayar copias con confirmación explícita."""
    import subprocess
    carpeta=Path.home()/'NEXORA_QWEN_RESULTADOS'
    if not (carpeta/'RESULTADOS_QWEN.csv').is_file():
        print('Falta RESULTADOS_QWEN.csv en', carpeta)
        return
    print('\nAuditoría de resultados locales. No se enviarán archivos a Internet.')
    print('1. Solo auditoría (no lee originales)')
    print('2. Auditoría + copias verificadas y ensayo de restauración')
    op=modelos.ask('Opción [1/2, 0 volver]: ')
    if op not in ('1','2'):return
    script=Path(__file__).with_name('auditoria_copias.py')
    args=[sys.executable,str(script),'--resultados',str(carpeta)]
    if op=='1':args+=['--solo-auditoria']
    else:
        print('Se leerán únicamente archivos aprobados y se crearán COPIAS fuera del origen.')
        if modelos.ask('Escribí AUTORIZO COPIAS: ')!='AUTORIZO COPIAS':return
        args+=['--demostracion','--confirmo-copias']
    _correr(args)

def clasificar_aprobados():
    """Clasificación local de la muestra ya aprobada, sin tocar originales."""
    carpeta=Path.home()/'NEXORA_QWEN_RESULTADOS'
    mapping=carpeta/'MAPA_PRIVADO_NO_COMPARTIR.json'
    approved=carpeta/'APROBAR_MUESTRA.csv'
    if not mapping.is_file() or not approved.is_file():
        print('Primero prepará y aprobá una muestra con el procedimiento de NEXORA.');return
    if not manager.listo():
        print('No hay un servidor compatible listo en 127.0.0.1:8080.');return
    import json, csv, time
    try:
        info=json.loads(mapping.read_text(encoding='utf-8'))
        with approved.open(newline='',encoding='utf-8') as f:
            aprobados=sum(r.get('aprobado_para_lectura','').strip().upper()=='SI' for r in csv.DictReader(f))
        origen=Path(info['root']).resolve(strict=True)
    except (OSError,ValueError,KeyError) as e:
        print('Muestra inválida:',type(e).__name__);return
    if not 0<aprobados<=30:
        print('La muestra debe contener entre 1 y 30 archivos aprobados.');return
    print(f'Se leerán {aprobados} archivos aprobados desde {origen}.')
    print('Se usará únicamente el servidor HTTP local. No se moverán archivos.')
    if modelos.ask('Escribí CLASIFICAR LOCAL: ')!='CLASIFICAR LOCAL':return
    # Preservar resultados anteriores antes de iniciar; no sobrescribir sin copia.
    for nombre in ('RESULTADOS_QWEN.csv','RESUMEN_QWEN.json'):
        anterior=carpeta/nombre
        if anterior.is_file():
            import shutil
            respaldo=carpeta/(anterior.stem+'_RESPALDO_'+time.strftime('%Y%m%d_%H%M%S')+anterior.suffix)
            shutil.copy2(anterior,respaldo)
    script=Path(__file__).with_name('clasificador_local.py')
    cmd=[sys.executable,str(script),'evaluar',str(origen),'--salida',str(carpeta),
         '--confirmo-lectura-local','--modelo','local','--max-aprobados','30']
    _correr(cmd)

def _vista_previa(rows,mode):
    """Muestra el árbol propuesto: grupo → tipo → cantidad (y ejemplos en modo personal)."""
    from collections import Counter,defaultdict
    from .organizador_final import CATEGORIES
    arbol=defaultdict(Counter);ejemplos=defaultdict(list)
    for r in rows:
        g=r.get('grupo') or '';arbol[g][CATEGORIES[r['categoria']]]+=1
        if len(ejemplos[g])<3:ejemplos[g].append(Path(r['ruta_relativa']).name[:50])
    print('\nVista previa de ORGANIZADOS/:')
    for g in sorted(arbol,key=lambda k:(-sum(arbol[k].values()),k)):
        tipos=', '.join(f'{t} {n}' for t,n in arbol[g].most_common())
        if g:print(f'  {g}/  ({sum(arbol[g].values())})  →  {tipos}')
        else:print(f'  {tipos}')
        if g and mode=='personal':print('      ej.:',' | '.join(ejemplos[g]))

def _simular(root,mode,rows,output):
    """Simulación: calcula duplicados reales (SHA-256) y destinos finales sin crear ni un archivo."""
    from .organizador_final import simulate, espacio_libre, MARGEN_BYTES
    print('\nSIMULACIÓN: leyendo originales para detectar duplicados (no se escribe nada)...')
    r=simulate(root,mode,rows,avance=lambda n,t:print(f'  {n}/{t}',flush=True))
    libre=espacio_libre(output.parent);necesario=r['bytes_necesarios']
    print('\nResultado de la simulación')
    print(f"  Se copiarían:            {len(r['archivos'])} archivos")
    print(f"  Duplicados exactos:      {len(r['duplicados'])} (no se copiarían)")
    print(f"  Espacio necesario:       {necesario/1024**2:.1f} MiB")
    print(f"  Espacio libre en disco:  {libre/1024**3:.1f} GiB  →  {'OK' if libre>=necesario+MARGEN_BYTES else 'INSUFICIENTE'}")
    if r['errores']:print(f"  No se podrían leer:      {len(r['errores'])}")
    if modelos.ask('¿Ver la lista completa de destinos? [s/N]: ').lower() in ('s','si','sí'):
        for e in sorted(r['archivos'],key=lambda e:e['destino'].casefold()):
            origen=f"   ←  {e['origen_relativo']}" if mode=='personal' else ''
            print(f"  {e['destino']}{origen}")
        for d in r['duplicados']:
            print(f"  (duplicado, no se copia) {d.get('origen_relativo','')}  =  {d['igual_a']}")

def organizar_carpeta_libre():
    from .organizador_final import check_root, plan, execute, _safe_destination, agrupar, simulate, espacio_libre, MARGEN_BYTES
    import time
    print('\nNEXORA — Organizar COPIAS de una carpeta elegida')
    print('1. Personal (conservar nombres)  2. Laboratorio anónimo (solo nombres)  0. Volver')
    op=modelos.ask('Opción: ')
    if op not in ('1','2'):return
    mode='personal' if op=='1' else 'anonimo'
    print('ATENCIÓN: anonimizar nombres NO elimina datos personales del contenido.')
    origen=modelos.ask('Ruta de la carpeta de origen: ').strip().strip('"\'')
    try:root=check_root(origen)
    except (OSError,ValueError) as e:print('Origen inválido:',e);return
    print('\n¿Cómo querés organizar?')
    print('  1. Por tipo (Imagenes, Videos, Documentos...)            sin IA')
    print('  2. Por tipo, con Qwen revisando archivos de texto        IA')
    print('  3. Por PROYECTO según nombres de archivo → Proyecto/Tipo IA')
    print('  4. Por carpeta de origen → Carpeta/Tipo                  sin IA')
    print('  5. Por fecha de modificación → Año/Mes/Tipo              sin IA')
    print('  6. Por fecha en que se TOMÓ la foto (cámara) → Año/Mes   sin IA')
    print('  7. Por lo que MUESTRAN las fotos y videos → Proyecto/Tipo IA mira')
    choice=modelos.ask('Criterio: ')
    criterios={'1':('tipo',False),'2':('tipo',True),'3':('proyecto_ia',False),'4':('carpeta',False),'5':('fecha',False),
               '6':('fecha_foto',False),'7':('contenido_ia',False)}
    if choice not in criterios:return
    criterio,ai=criterios[choice]
    if criterio=='contenido_ia':
        from . import vision
        if vision.herramienta_disponible() is None:
            print('Para que Qwen vea fotos hace falta ffmpeg, Pillow o sips (macOS).');return
        if manager.listo() and not manager.vision and vision.servidor_con_vision() is False:
            print('El servidor está activo pero SIN visión. Detenelo (5) y reinicialo (1) activando mmproj.');return
    if (ai or criterio in ('proyecto_ia','contenido_ia')) and not manager.listo():
        print('Primero iniciá el servidor local (opción 1) y esperá a que esté Listo.');return
    print('Analizando hasta 1000 archivos, máximo 100 MiB por archivo y 1 GiB total...')
    try:
        omitidos=[]
        rows,skipped,total=plan(root,use_ai=ai,omitidos=omitidos)
        print(f'Archivos: {len(rows)}  Omitidos: {skipped}  Tamaño: {total/1024**2:.1f} MiB')
        for rel,motivo in omitidos[:6]:
            nombre=Path(rel).name[:45] if mode=='personal' else 'archivo'+Path(rel).suffix
            print(f'  omitido  {nombre:<45}  {motivo}')
        if len(omitidos)>6:print(f'  ... y {len(omitidos)-6} más')
        if not rows:print('No hay archivos para organizar.');return
        if criterio=='contenido_ia':
            from . import vision
            n=sum(Path(r['ruta_relativa']).suffix.lower() in vision.EXT_IMAGEN|vision.EXT_VIDEO for r in rows)
            print(f'Qwen va a MIRAR hasta {min(n,vision.MAX_IMAGENES)} fotos/videos (reducidos en memoria; no se escribe nada).')
            if n>vision.MAX_IMAGENES:print(f'  Límite {vision.MAX_IMAGENES}: el resto se agrupa solo por nombre.')
            def _av(i,t,resta):
                if i<=3 or i%10==0 or i==t:print(f'  vistas {i}/{t}  (faltan ~{resta/60:.1f} min)',flush=True)
            from .organizador_final import huellas
            huellas(root,rows)  # duplicados exactos: Qwen mira una sola vez cada foto
            res=vision.describir_todo(root,rows,avance=_av)
            print(f"  Descritas: {res['descritas']}  No se pudieron ver: {res['fallidas']}  ({res['segundos']:.0f} s)")
            if mode=='personal':
                for r in [r for r in rows if r.get('visto')][:5]:print(f"  {Path(r['ruta_relativa']).name[:40]:<40} → «{r['visto']}»")
        if criterio=='fecha_foto':
            info=agrupar(rows,criterio,mode,root=root)
            print(f"Fecha de la cámara (EXIF): {info['con_fecha_camara']}   Fecha del archivo: {info['con_fecha_archivo']}")
        elif criterio in ('proyecto_ia','contenido_ia'):
            print('Qwen está agrupando por proyecto' + (' con lo que vio en cada imagen...' if criterio=='contenido_ia' else ' leyendo SOLO los nombres (no el contenido)...'))
            t0=time.time()
            info=agrupar(rows,criterio,mode,avance=lambda n,t:print(f'  asignados {n}/{t}',flush=True),root=root)
            usados={r['grupo'] for r in rows}
            print(f"Proyectos propuestos por Qwen: {', '.join(info['proyectos'])}  ({time.time()-t0:.0f} s)")
            vacios=[p for p in info['proyectos'] if p not in usados]
            if vacios and mode=='personal':print('  Sin archivos asignados (no se crean):',', '.join(vacios))
            if info['lotes_fallidos']:print(f"Aviso: {info['lotes_fallidos']} lote(s) sin respuesta válida → esos archivos quedan en Otros.")
        else:agrupar(rows,criterio,mode)
        _vista_previa(rows,mode)
        revisar=[r for r in rows if r['categoria']=='revisar']
        if revisar:
            print(f'\nEn Revisar ({len(revisar)}): NEXORA no decide sola cuando hay dudas.')
            for r in revisar[:8]:
                nombre=Path(r['ruta_relativa']).name[:45] if mode=='personal' else 'archivo'+Path(r['ruta_relativa']).suffix
                print(f"  {nombre:<45}  {r.get('motivo','')}")
            if len(revisar)>8:print(f'  ... y {len(revisar)-8} más')
        output=root.parent/(root.name+'_NEXORA_'+mode+'_'+time.strftime('%Y%m%d_%H%M%S'))
        _safe_destination(root,output)
        print('\nSalida NUEVA:',output)
        print('Los originales NO serán modificados ni borrados.')
        print('\n  SIMULAR      → ver el resultado exacto sin escribir NADA en el disco')
        print('  CREAR COPIAS → crear las copias de verdad')
        print('  Enter        → cancelar')
        respuesta=modelos.ask('Elegí: ')
        if respuesta.upper()=='SIMULAR':
            _simular(root,mode,rows,output)
            respuesta=modelos.ask('\nEscribí CREAR COPIAS para hacerlo de verdad (Enter para salir): ')
        if respuesta!='CREAR COPIAS':print('Listo, no se escribió nada.');return
        summary=execute(root,output,mode,rows,skipped,total)
        print('\nFINALIZADO')
        print(f"  Copiados y verificados (SHA-256): {summary['archivos_copiados']}")
        print(f"  Duplicados exactos no copiados:   {summary['duplicados_exactos_no_copiados']}")
        print(f"  Omitidos (ocultos/sensibles/enlaces): {summary['archivos_omitidos']}")
        print(f"  Errores de copia:                 {summary['errores_copia']}")
        print(f"  Originales modificados:           {summary['originales_modificados_por_nexora']}")
        print('  Detalle: RESUMEN.json y MANIFIESTO_PRIVADO.json (no compartir el manifiesto).')
        print('Abrí la carpeta:',output/'ORGANIZADOS')
        print('Revisá las copias antes de decidir qué hacer con el origen.')
    except (OSError,ValueError,FileExistsError,KeyError) as e:print('Operación detenida:',e)

def main():
    _activar_grabacion()
    print('NEXORA — ORGANIZADOR INTELIGENTE DE ARCHIVOS (BETA)')
    if isinstance(sys.stdout,_Grabacion):print('[modo grabación: rutas personales ocultas]')
    print('Un proyecto de Pieza por Pieza.')
    try:
        while True:
            print('\n1. Preparar modelo local  2. Estado del servidor  3. Ver registros')
            print('4. Configuración avanzada  5. Detener servidor propio')
            print('6. Demostración segura: ordenar y revertir 30 archivos ficticios')
            print('7. Auditar Qwen y organizar COPIAS verificadas')
            print('8. Clasificar muestra aprobada con Qwen LOCAL')
            print('9. Organizar COPIAS de cualquier carpeta  0. Salir')
            op=modelos.ask('Opción: ')
            if op=='0':return
            try:
                if op=='1':configurar_servidor()
                elif op=='2':print('Estado:',manager.estado()+(' (con visión)' if manager.vision and manager.estado()=='Listo' else ''))
                elif op=='3':print(manager.ultimas_lineas())
                elif op=='4':modelos.settings_menu(settings);guardar_config();_activar_grabacion()
                elif op=='5':print('Servidor propio detenido.' if manager.detener() else 'No hay servidor propio que detener.')
                elif op=='6':laboratorio()
                elif op=='7':auditoria_copias()
                elif op=='8':clasificar_aprobados()
                elif op=='9':organizar_carpeta_libre()
                else:print('Opción no reconocida.')
            except (OSError,ValueError,RuntimeError) as e:
                print('Error:',e)
    finally:
        if manager.proceso is not None:
            print('Cerrando el servidor iniciado por esta sesión...')
            manager.detener()

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nCancelado.')
