#!/usr/bin/env python3
"""NEXORA: auditoría y demostración reversible de COPIAS; biblioteca estándar."""
import argparse,csv,hashlib,json,os,pathlib,shutil,stat,tempfile,time
from collections import Counter
CATS={'codigo','datos','documento','subtitulos','revisar'}
BLOCK={'secrets','secret','private','privado','credentials','credenciales','token','tokens','password','passwords','.env','.git','node_modules','.venv','venv','ssh','keys','key','cookies','cookie','backup','backups'}
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def valid(rel):
 p=pathlib.PurePosixPath(rel)
 return bool(rel) and not p.is_absolute() and '..' not in p.parts and all(x.lower() not in BLOCK and not x.startswith('.') and not any(z in x.lower() for z in ('secret','password','credential','token')) for x in p.parts)
def writejson(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 a=argparse.ArgumentParser(description='Auditar resultados de Qwen y ensayar organización sobre copias, sin modificar originales')
 a.add_argument('--resultados',default=str(pathlib.Path.home()/'NEXORA_QWEN_RESULTADOS'))
 a.add_argument('--solo-auditoria',action='store_true',help='No leer ni copiar archivos fuente')
 a.add_argument('--demostracion',action='store_true',help='Permite copiar archivos aprobados a un laboratorio aislado')
 a.add_argument('--confirmo-copias',action='store_true',help='Confirmo copiar exclusivamente archivos aprobados')
 a.add_argument('--max-bytes',type=int,default=16384)
 args=a.parse_args()
 if args.solo_auditoria and args.demostracion:a.error('Elegí una modalidad')
 out=pathlib.Path(args.resultados).expanduser().resolve(strict=True)
 results=out/'RESULTADOS_QWEN.csv'; approved=out/'APROBAR_MUESTRA.csv'; mapping=out/'MAPA_PRIVADO_NO_COMPARTIR.json'
 if not results.is_file():a.error('No existe RESULTADOS_QWEN.csv')
 with results.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
 if not rows:a.error('CSV vacío')
 ids=[r['id'] for r in rows]
 if len(ids)!=len(set(ids)):a.error('IDs duplicados')
 if any(r['categoria_qwen'] not in CATS or r['categoria_extension'] not in CATS for r in rows):a.error('Categorías inesperadas')
 disagreements=[r for r in rows if r['categoria_extension']!=r['categoria_qwen']]
 matched=[r for r in rows if r['categoria_extension']==r['categoria_qwen'] and r['categoria_qwen']!='revisar']
 human=[r for r in rows if r.get('categoria_humana','') in CATS]
 audit={'procesados':len(rows),'categorias_qwen':dict(Counter(r['categoria_qwen'] for r in rows)),'cobertura':round(sum(r['categoria_qwen']!='revisar' for r in rows)/len(rows),4),'coincidencias_con_reglas':len(matched),'desacuerdos_con_reglas':len(disagreements),'exactitud_humana':'NO MEDIDA' if not human else {'aciertos':sum(r['categoria_humana']==r['categoria_qwen'] for r in human),'evaluados':len(human)},'nota':'Coincidir con reglas NO demuestra exactitud; revisar discrepancias manualmente.'}
 run=out/('NEXORA_CIERRE_'+time.strftime('%Y%m%d_%H%M%S'))
 if run.exists():a.error('Carpeta de salida ya existe; reintentá')
 run.mkdir(mode=0o700)
 writejson(run/'AUDITORIA.json',audit)
 with (run/'DESACUERDOS.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['id','extension','categoria_extension','categoria_qwen','confianza','categoria_humana']);w.writeheader()
  for r in disagreements:w.writerow({k:r.get(k,'') for k in w.fieldnames})
 print('AUDITORÍA:',json.dumps(audit,ensure_ascii=False))
 print('Reporte:',run/'AUDITORIA.json')
 if not args.demostracion:
  print('Modo auditoría: ninguna copia realizada. Para ensayar copias: --demostracion --confirmo-copias')
  return
 if not args.confirmo_copias:a.error('Falta --confirmo-copias; auditoría creada, ninguna copia realizada')
 if not approved.is_file() or not mapping.is_file():a.error('Faltan aprobación o mapa privado; ninguna copia realizada')
 with approved.open(newline='',encoding='utf-8') as f:arows={r['id']:r for r in csv.DictReader(f)}
 mp=json.loads(mapping.read_text(encoding='utf-8'))
 root=pathlib.Path(mp['root']).resolve(strict=True)
 if not root.is_dir():a.error('Carpeta original no existe')
 if root==out or root in out.parents or out in root.parents:a.error('Carpetas fuente y salida deben estar separadas')
 if args.max_bytes<=0 or args.max_bytes>1024*1024:a.error('Límite de tamaño inválido')
 demo=run/'LABORATORIO_COPIAS';demo.mkdir(mode=0o700)
 manifest=[];skips=Counter()
 for r in rows:
  key=r['id'];cat=r['categoria_qwen']
  if cat=='revisar':skips['revisar']+=1;continue
  if r['categoria_extension']!=cat:skips['desacuerdo_reglas']+=1;continue
  if r.get('confianza')!='alta':skips['confianza_no_alta']+=1;continue
  if arows.get(key,{}).get('aprobado_para_lectura','').strip().upper()!='SI':skips['no_aprobado']+=1;continue
  rel=mp.get('files',{}).get(key)
  if not rel or not valid(rel) or hashlib.sha256(rel.encode('utf-8','surrogateescape')).hexdigest()[:20]!=key:skips['ruta_invalida']+=1;continue
  source=root/rel
  try:
   cur=root
   for part in pathlib.PurePosixPath(rel).parts:
    cur=cur/part
    if cur.is_symlink():raise ValueError('symlink')
   if not source.resolve(strict=True).is_relative_to(root):raise ValueError('fuera de fuente')
   st=source.lstat()
   if not stat.S_ISREG(st.st_mode) or not 0<st.st_size<=args.max_bytes:raise ValueError('tipo o tamaño')
   # Abrir sin seguir symlinks y copiar bytes del descriptor validado.
   fd=os.open(source,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
   try:
    fst=os.fstat(fd)
    if not stat.S_ISREG(fst.st_mode) or fst.st_size!=st.st_size or fst.st_size>args.max_bytes:raise ValueError('cambio de archivo')
    with os.fdopen(fd,'rb',closefd=False) as src:data=src.read(args.max_bytes+1)
   finally:os.close(fd)
   if len(data)!=st.st_size or b'\0' in data:raise ValueError('binario/cambio')
   data.decode('utf-8','strict')
   target=demo/cat/(key+source.suffix.lower())
   target.parent.mkdir(exist_ok=True)
   with target.open('xb') as f:f.write(data)
   sha=hashlib.sha256(data).hexdigest()
   if digest(target)!=sha:raise ValueError('hash de copia incorrecto')
   manifest.append({'id':key,'categoria':cat,'archivo_copia':str(target.relative_to(run)),'sha256':sha,'bytes':len(data)})
  except (OSError,ValueError,UnicodeError) as e:skips['lectura_o_validacion']+=1
 writejson(run/'MANIFIESTO_COPIAS.json',{'copias':manifest,'omitidos':dict(skips),'origenes_modificados':0})
 print('COPIAS VERIFICADAS:',len(manifest),'OMITIDOS:',dict(skips))
 # Deshacer la organización en una COPIA del laboratorio, nunca tocar fuentes.
 undo=run/'PRUEBA_REVERSA';undo.mkdir(mode=0o700)
 ok=0
 for x in manifest:
  src=run/x['archivo_copia'];dst=undo/pathlib.Path(x['archivo_copia']).name
  shutil.copyfile(src,dst)
  if digest(dst)!=x['sha256']:raise RuntimeError('Falló verificación de reversión')
  ok+=1
 writejson(run/'REVERSION_VERIFICADA.json',{'copias_reconstruidas':ok,'hashes_coincidentes':ok,'origenes_modificados':0,'aclaracion':'Ensayo de restauración de copias; NO revierte movimientos reales ni modifica originales.'})
 print('RESTAURACIÓN DE COPIAS VERIFICADA:',ok)
 print('Carpeta del laboratorio:',run)
 print('IMPORTANTE: esto NO integra aún el menú ni demuestra exactitud.')
if __name__=='__main__':main()
