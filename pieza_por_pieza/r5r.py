#!/usr/bin/env python3
"""R5-R: laboratorio sintético autocontenido, sin permisos para rutas externas."""
import argparse, hashlib, json, os, pathlib, shutil, sqlite3, stat, sys, uuid
from datetime import datetime, timezone

CATEGORIES = ('universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos')
SAMPLES = [
 ('universidad','Notas sobre el calendario de examenes y el curso.'),
 ('finanzas','Resumen de presupuesto mensual y facturas.'),
 ('fotografias','Inventario de fotos de paisajes y encuadres.'),
 ('programacion','Descripcion de una funcion Python y sus pruebas.'),
 ('trabajo','Agenda de reunion de equipo y entregables.'),
 ('ciencia','Registro de observaciones del experimento.'),
 ('entretenimiento','Lista de peliculas y recomendaciones.'),
 ('miscelaneos','Recordatorio de comprar cortinas para la casa.'),
]
MARKER='R5R_SYNTHETIC_LAB_V1'

def digest(b): return hashlib.sha256(b).hexdigest()
def filehash(p): return digest(p.read_bytes())
def write_json(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def root_path(raw):
 p=pathlib.Path(raw).expanduser().absolute()
 if p.is_symlink(): raise ValueError('La raiz no puede ser un enlace simbolico')
 return p

def ensure_lab(root):
 if not root.is_dir() or root.is_symlink() or not (root/'.r5r_lab').is_file(): raise ValueError('No es un laboratorio R5-R valido')
 if (root/'.r5r_lab').read_text().strip()!=MARKER: raise ValueError('Marcador de laboratorio invalido')
 for part in ('inbox','sorted','state'):
  p=root/part
  if not p.is_dir() or p.is_symlink(): raise ValueError('Directorio inseguro: '+part)
 return root

def safe_file(root,rel,exists=True):
 if not isinstance(rel,str) or not rel or '\\' in rel or '\x00' in rel: raise ValueError('Ruta invalida')
 pp=pathlib.PurePosixPath(rel)
 if pp.is_absolute() or any(x in ('..','.') for x in rel.split('/')): raise ValueError('Ruta fuera del laboratorio')
 p=root.joinpath(*pp.parts)
 for x in [root,*list(p.relative_to(root).parts)[:0]]: pass
 current=root
 for piece in pp.parts:
  current=current/piece
  if current.is_symlink(): raise ValueError('Enlace simbolico rechazado')
 if exists:
  s=p.lstat()
  if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1: raise ValueError('Archivo no regular o con hardlinks')
 return p

def db(root):
 c=sqlite3.connect(root/'state'/'audit.sqlite')
 c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, utc TEXT, event TEXT, filename TEXT, detail TEXT)')
 c.commit();return c

def log(c,event,name='',detail=''):
 c.execute('INSERT INTO events(utc,event,filename,detail) VALUES (?,?,?,?)',(datetime.now(timezone.utc).isoformat(),event,name,detail));c.commit()

def setup(args):
 root=root_path(args.root)
 if root.exists(): raise ValueError('La carpeta ya existe; no se sobrescribe nada')
 root.mkdir(parents=True,mode=0o700)
 try:
  (root/'.r5r_lab').write_text(MARKER+'\n')
  for d in ('inbox','sorted','state'): (root/d).mkdir(mode=0o700)
  truth=[]
  for i in range(30):
   cat,content=SAMPLES[i%len(SAMPLES)]
   name=f'doc_{i+1:03d}.txt'
   p=root/'inbox'/name
   p.write_text(f'DOCUMENTO SINTETICO {i+1}\n{content}\n',encoding='utf-8')
   truth.append({'file':name,'category':cat,'sha256':filehash(p)})
  write_json(root/'state'/'synthetic_reference.json',truth)
  c=db(root);log(c,'PREPARE',detail='30 documentos ficticios');c.close()
 except Exception:
  shutil.rmtree(root);raise
 print('PREPARADO: 30 documentos sinteticos; carpeta exclusiva:',root)

def plan(args):
 root=ensure_lab(root_path(args.root))
 if (root/'state'/'plan.json').exists(): raise ValueError('Ya existe plan: no sobrescribir')
 ref=json.loads((root/'state'/'synthetic_reference.json').read_text())
 actions=[]
 for item in ref:
  name=item['file'];src=safe_file(root,'inbox/'+name)
  if filehash(src)!=item['sha256']: raise ValueError('Hash alterado: '+name)
  cat=item['category']
  if cat not in CATEGORIES: raise ValueError('Categoria invalida')
  actions.append({'source':'inbox/'+name,'destination':'sorted/'+cat+'/'+name,'sha256':item['sha256']})
 payload={'schema':'r5r-plan-v1','actions':actions,'source':'DEMO_SYNTHETIC_REFERENCE_NOT_MODEL'}
 payload['plan_sha256']=digest(json.dumps(payload,sort_keys=True,separators=(',',':')).encode())
 write_json(root/'state'/'plan.json',payload)
 c=db(root);log(c,'PLAN',detail=payload['plan_sha256']);c.close()
 print('PLAN: 30 movimientos propuestos; origen: referencia sintetica, NO predicciones Qwen')
 print('DIGEST:',payload['plan_sha256'])

def getplan(root):
 p=json.loads((root/'state'/'plan.json').read_text())
 sha=p.pop('plan_sha256')
 actual=digest(json.dumps(p,sort_keys=True,separators=(',',':')).encode())
 if sha!=actual or p.get('schema')!='r5r-plan-v1': raise ValueError('Plan alterado')
 p['plan_sha256']=sha
 seen=set()
 for a in p['actions']:
  src=a['source'];dst=a['destination'];parts=dst.split('/')
  if len(parts)!=3 or parts[0]!='sorted' or parts[1] not in CATEGORIES or src!='inbox/'+parts[2]: raise ValueError('Ruta del plan invalida')
  if src in seen: raise ValueError('Duplicado');seen.add(src)
  if len(a['sha256'])!=64: raise ValueError('Hash invalido')
 return p

def approve(args):
 root=ensure_lab(root_path(args.root));p=getplan(root)
 if (root/'state'/'approval.json').exists(): raise ValueError('Ya hay aprobacion')
 if args.digest!=p['plan_sha256']: raise ValueError('Digest no coincide: aprobacion denegada')
 if args.confirm!='AUTORIZO DEMO R5R': raise ValueError('Frase de autorizacion incorrecta')
 write_json(root/'state'/'approval.json',{'plan_sha256':p['plan_sha256'],'authorization':'explicit_demo_only'})
 c=db(root);log(c,'APPROVE',detail=p['plan_sha256']);c.close()
 print('AUTORIZADO: plan de demostracion; ningun movimiento aun')

def move(root,source,destination,sha):
 src=safe_file(root,source);dst=safe_file(root,destination,False)
 if not src.is_file() or filehash(src)!=sha: raise ValueError('Origen modificado o inexistente: '+source)
 if dst.exists() or dst.is_symlink(): raise ValueError('Destino ocupado: '+destination)
 if not dst.parent.parent.is_dir() or dst.parent.parent.is_symlink(): raise ValueError('Padre invalido')
 dst.parent.mkdir(exist_ok=True,mode=0o700)
 if dst.parent.is_symlink(): raise ValueError('Destino enlazado')
 # os.rename nunca sobrescribe porque comprobamos antes, pero NO es una defensa TOCTOU adversarial.
 os.rename(src,dst)
 if filehash(dst)!=sha: raise ValueError('Hash post-movimiento incorrecto')

def execute(args):
 root=ensure_lab(root_path(args.root));p=getplan(root)
 approval=json.loads((root/'state'/'approval.json').read_text()) if (root/'state'/'approval.json').exists() else {}
 if approval.get('plan_sha256')!=p['plan_sha256']: raise ValueError('Sin autorizacion valida')
 c=db(root)
 done=0
 for a in p['actions']:
  src=root/a['source'];dst=root/a['destination']
  if dst.exists() and not src.exists() and filehash(safe_file(root,a['destination']))==a['sha256']:
   continue
  move(root,a['source'],a['destination'],a['sha256'])
  log(c,'MOVE',a['source'],a['destination']);done+=1
 c.close();print(f'EJECUTADO: {done} movimientos nuevos; aprobacion verificada')

def rollback(args):
 root=ensure_lab(root_path(args.root));p=getplan(root)
 c=db(root);count=0
 for a in reversed(p['actions']):
  dst=root/a['destination'];src=root/a['source']
  if src.exists() and not dst.exists():
   if filehash(safe_file(root,a['source']))!=a['sha256']: raise ValueError('Origen alterado')
   continue
  move(root,a['destination'],a['source'],a['sha256'])
  log(c,'ROLLBACK',a['source'],a['destination']);count+=1
 c.close();print(f'REVERTIDO: {count} movimientos; hashes verificados')

def verify(args):
 root=ensure_lab(root_path(args.root));p=getplan(root)
 inside=outside=0
 for a in p['actions']:
  src=root/a['source'];dst=root/a['destination']
  if src.exists() and not dst.exists():
   if filehash(safe_file(root,a['source']))!=a['sha256']: raise ValueError('Hash origen incorrecto')
   inside+=1
  elif dst.exists() and not src.exists():
   if filehash(safe_file(root,a['destination']))!=a['sha256']: raise ValueError('Hash destino incorrecto')
   outside+=1
  else: raise ValueError('Archivo duplicado o faltante: '+a['source'])
 print(f'VERIFICADO: inbox={inside}, sorted={outside}, total={inside+outside}, hashes correctos')

def main():
 ap=argparse.ArgumentParser(description='R5-R laboratorio reversible solo datos sinteticos')
 sub=ap.add_subparsers(dest='cmd',required=True)
 for cmd in ('prepare','plan','approve','execute','rollback','verify'):
  sp=sub.add_parser(cmd);sp.add_argument('--root',default='./r5r_demo_lab')
  if cmd=='approve':sp.add_argument('--digest',required=True);sp.add_argument('--confirm',required=True)
 args=ap.parse_args()
 try: globals()[{'prepare':'setup'}.get(args.cmd,args.cmd)](args)
 except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
  print('ERROR:',e,file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
