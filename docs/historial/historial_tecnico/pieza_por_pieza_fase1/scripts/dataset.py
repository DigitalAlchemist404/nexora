#!/usr/bin/env python3
"""Pieza por Pieza: reproducible synthetic dataset. Standard library only."""
import argparse, csv, hashlib, io, json, os, random, struct, sys, zlib
from pathlib import Path

COUNTS = [('universidad',180),('finanzas',120),('fotografias',160),('programacion',150),('trabajo',120),('ciencia',100),('entretenimiento',90),('miscelaneos',80)]
FORMATS = ('txt','md','csv','json','pdf','png')
MAGIC = b'\x89PNG\r\n\x1a\n'

def sha256(b): return hashlib.sha256(b).hexdigest()
def pdf_bytes(title, body):
    def safe(s): return s.encode('ascii','replace').decode('ascii').replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream = f'BT /F1 13 Tf 40 760 Td ({safe(title)}) Tj 0 -24 Td /F1 10 Tf ({safe(body[:110])}) Tj ET'.encode('ascii')
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    out=bytearray(b'%PDF-1.4\n'); offsets=[0]
    for i,obj in enumerate(objs,1):
        offsets.append(len(out)); out.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(out);out.extend(f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode())
    for pos in offsets[1:]:out.extend(f'{pos:010d} 00000 n \n'.encode())
    out.extend(f'trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode());return bytes(out)
def png_chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png_bytes(seed):
    r=random.Random(seed);width=16;height=16
    rows=b''.join(b'\x00'+bytes(c for _ in range(width) for c in (r.randrange(256),r.randrange(256),r.randrange(256))) for _ in range(height))
    return MAGIC+png_chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+png_chunk(b'IDAT',zlib.compress(rows,9))+png_chunk(b'IEND',b'')
def content(category,idx,ext,seed,difficulty):
    label=f'{category} expediente {idx:04d}'; body=f'Documento sintetico para laboratorio. Categoria: {category}. Registro {idx}. Semilla {seed}. Dificultad {difficulty}.'
    if ext=='txt':return (label+'\n'+body+'\n').encode()
    if ext=='md':return ('# '+label+'\n\n'+body+'\n').encode()
    if ext=='csv':return ('categoria,registro,semilla,dificultad\n'+f'{category},{idx},{seed},{difficulty}\n').encode()
    if ext=='json':return (json.dumps({'categoria':category,'registro':idx,'semilla':seed,'dificultad':difficulty},sort_keys=True,ensure_ascii=False)+'\n').encode()
    if ext=='pdf':return pdf_bytes(label,body)
    return png_bytes(seed*100000+idx)
def plan(seed):
    r=random.Random(seed);items=[];serial=0
    for category,count in COUNTS:
        for n in range(1,count+1):
            serial+=1;ext=FORMATS[(serial-1)%len(FORMATS)]
            difficulty='ambiguo' if serial%11==0 else 'normal'
            # Names do not always reveal category, so a classifier cannot always use filenames alone.
            name=(f'archivo_{serial:04d}' if difficulty=='ambiguo' else f'{category}_{serial:04d}')+'.'+ext
            data=content(category,serial,ext,seed,difficulty)
            items.append((name,category,ext,difficulty,data))
    r.shuffle(items)
    return items

def safe_root(path):
    p=Path(path).expanduser().absolute()
    if p == Path('/') or p == Path.home() or len(p.parts)<3:raise ValueError('Ruta de laboratorio insegura')
    if p.is_symlink():raise ValueError('No se permite raiz simbolica')
    return p

def generate(root,seed):
    if root.exists():
        raise RuntimeError('Destino ya existe; no se sobrescribe. Elegi una carpeta nueva.')
    if root.parent.exists() and root.parent.is_symlink():raise RuntimeError('Directorio padre simbolico no permitido')
    root.mkdir(parents=True,exist_ok=False)
    dataset=root/'dataset'; dataset.mkdir(); reference=root/'reference';reference.mkdir()
    rows=[]
    for i,(name,cat,ext,difficulty,data) in enumerate(plan(seed),1):
        file=dataset/name
        with file.open('xb') as f:f.write(data)
        rows.append({'id':f'{i:04d}','nombre':name,'formato':ext,'categoria_esperada':cat,'ruta_original':name,'sha256':sha256(data),'dificultad':difficulty,'semilla':seed})
    with (reference/'manifest.json').open('x',encoding='utf-8') as f:json.dump({'schema_version':1,'seed':seed,'files':rows},f,indent=2,ensure_ascii=False)
    print(f'OK: {len(rows)} archivos; manifiesto separado en {reference}/manifest.json')

def validate(root):
    manifest=root/'reference'/'manifest.json';dataset=root/'dataset'
    obj=json.loads(manifest.read_text(encoding='utf-8')); rows=obj['files']
    if len(rows)!=1000:raise ValueError(f'Manifiesto: {len(rows)} registros, no 1000')
    counts={k:0 for k,_ in COUNTS}; seen=set()
    for row in rows:
        name=row['nombre'];p=Path(name)
        if p.name!=name or name in seen or p.suffix.lstrip('.')!=row['formato'] or row['formato'] not in FORMATS:raise ValueError(f'Entrada invalida: {name}')
        seen.add(name); counts[row['categoria_esperada']]+=1
        data=(dataset/name).read_bytes()
        if sha256(data)!=row['sha256']:raise ValueError(f'Hash incorrecto: {name}')
        ext=row['formato']
        if ext=='png':
            if not data.startswith(MAGIC) or not data.endswith(png_chunk(b'IEND',b'')):raise ValueError('PNG invalido')
            # Validate compressed pixel payload and CRCs.
            off=8; idat=b''; found_ihdr=False
            while off<len(data):
                if off+12>len(data):raise ValueError('PNG truncado')
                n=struct.unpack('>I',data[off:off+4])[0];typ=data[off+4:off+8];chunk=data[off+8:off+8+n]
                crc=struct.unpack('>I',data[off+8+n:off+12+n])[0]
                if zlib.crc32(typ+chunk)&0xffffffff!=crc:raise ValueError('PNG CRC invalido')
                if typ==b'IHDR':found_ihdr=True
                if typ==b'IDAT':idat+=chunk
                off+=12+n
            if not found_ihdr or len(zlib.decompress(idat))!=16*(1+16*3):raise ValueError('PNG datos invalidos')
        elif ext=='pdf':
            if not data.startswith(b'%PDF-1.4\n') or b'startxref\n' not in data or not data.endswith(b'%%EOF\n'):raise ValueError('PDF invalido')
            xref=int(data.rsplit(b'startxref\n',1)[1].split(b'\n',1)[0]);
            if data[xref:xref+4]!=b'xref':raise ValueError('PDF xref invalido')
        elif ext=='json':json.loads(data)
        elif ext=='csv':
            parsed=list(csv.DictReader(io.StringIO(data.decode('utf-8'))))
            if len(parsed)!=1:raise ValueError('CSV invalido')
        else:data.decode('utf-8')
    expected=dict(COUNTS)
    if counts!=expected:raise ValueError(f'Distribucion incorrecta: {counts}')
    actual={p.name for p in dataset.iterdir() if p.is_file()}
    if actual!=seen:raise ValueError('Archivos extra o faltantes')
    # Regenerate in memory to check seed and deterministic bytes.
    regenerated={name:sha256(data) for name,_,_,_,data in plan(obj['seed'])}
    if regenerated!={row['nombre']:row['sha256'] for row in rows}:raise ValueError('No coincide con la semilla')
    print('OK: 1000 archivos, formatos, CRC/hash, distribucion y reproducibilidad validados')
    print('Categorias:',counts)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    for cmd in ('generate','validate'):
        s=sub.add_parser(cmd);s.add_argument('--root',required=True)
        if cmd=='generate':s.add_argument('--seed',type=int,default=20261105)
    args=p.parse_args()
    try:
        root=safe_root(args.root)
        if args.action=='generate':generate(root,args.seed)
        else:validate(root)
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);sys.exit(1)
if __name__=='__main__':main()
