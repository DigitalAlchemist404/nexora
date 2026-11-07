#!/usr/bin/env python3
"""R5-L: replay exploratorio de politica y nuevo conjunto ciego (stdlib)."""
import argparse, csv, hashlib, json, random, re, struct, zlib
from collections import Counter
from pathlib import Path

CATS=('universidad','finanzas','fotografias','programacion','trabajo','ciencia','entretenimiento','miscelaneos')
# Textos originales, sin etiquetas literales ni nombres de categoria.
TOPICS={
'universidad':[
'El docente publicó la rúbrica del ensayo y confirmó la fecha del examen final.',
'Los estudiantes revisaron el programa del curso antes de inscribir las materias.',
'La biblioteca prestará ejemplares de apoyo para el seminario de metodología.',
'El grupo presentó el proyecto de laboratorio y recibió observaciones del profesor.',
'La matrícula del semestre incluye tres asignaturas y un taller optativo.',
'El equipo de investigación estudiantil entregó el informe al departamento académico.',
'La tutoría del martes servirá para repasar ejercicios de cálculo diferencial.',
'El consejo estudiantil solicitó ampliar el horario de las salas de estudio.'],
'finanzas':[
'La conciliación bancaria mostró una diferencia entre el saldo y los movimientos.',
'El presupuesto trimestral reserva fondos para mantenimiento y gastos operativos.',
'La factura vencida se registró como cuenta por pagar en el libro auxiliar.',
'El flujo de caja proyectado disminuye durante el segundo mes del ejercicio.',
'La tasa de interés efectiva cambió el costo total del préstamo.',
'El estado de resultados presenta ingresos, costos y utilidad del período.',
'El auditor revisó comprobantes antes del cierre contable anual.',
'El pago de proveedores se programó después de verificar la liquidez disponible.'],
'fotografias':[
'La toma muestra una silueta a contraluz con exposición reducida.',
'El encuadre utiliza líneas diagonales para dirigir la mirada al sujeto.',
'La sesión se realizó con un lente de cincuenta milímetros y luz lateral.',
'El balance de blancos corrigió el tono cálido de la iluminación interior.',
'La composición deja espacio negativo sobre el horizonte.',
'El enfoque selectivo separa el primer plano del fondo desenfocado.',
'La cámara capturó la escena en formato RAW para conservar detalle.',
'La profundidad de campo disminuyó al abrir el diafragma.'],
'programacion':[
'La función devuelve una lista ordenada después de validar los argumentos.',
'El repositorio incorpora pruebas unitarias para el módulo de autenticación.',
'La excepción se produce cuando la clave no existe en el diccionario.',
'El compilador rechazó una conversión de tipos no permitida.',
'La revisión de código detectó una condición de carrera en dos hilos.',
'El servicio expone un endpoint que responde con objetos JSON.',
'El algoritmo recorre un árbol mediante una búsqueda en profundidad.',
'La nueva versión corrige un fallo de memoria en el proceso de serialización.'],
 'trabajo':[
'El equipo acordó los entregables de la semana durante la reunión de seguimiento.',
'La jefatura aprobó la solicitud de vacaciones para el próximo trimestre.',
'El cronograma de contratación contempla entrevistas y una evaluación técnica.',
'El área de operaciones actualizó el procedimiento de atención a clientes.',
'La minuta asigna responsables y fechas para cada actividad pendiente.',
'La capacitación interna se realizará durante la jornada del viernes.',
'El supervisor solicitó un reporte del avance de los indicadores mensuales.',
'El departamento coordinó turnos para cubrir la ausencia de dos colaboradores.'],
'ciencia':[
'El experimento comparó dos grupos y registró la temperatura cada minuto.',
'La hipótesis se evaluó mediante observaciones repetidas y análisis estadístico.',
'El microscopio permitió observar la estructura de las células de la muestra.',
'El equipo calibró el sensor antes de medir la concentración de partículas.',
'La publicación describe la metodología y las limitaciones del estudio.',
'La reacción química produjo un precipitado después de mezclar las soluciones.',
'Los datos del telescopio mostraron variaciones periódicas en la señal.',
'El protocolo exige repetir las mediciones para estimar la incertidumbre.'],
'entretenimiento':[
'La película estrenó su tráiler y anunció el reparto principal.',
'El concierto agotó las entradas antes de la presentación del sábado.',
'La crítica destacó la banda sonora y la actuación del protagonista.',
'El torneo de videojuegos reunió a equipos de varias regiones.',
'El festival publicó los horarios de sus escenarios musicales.',
'La nueva temporada de la serie tendrá ocho episodios.',
'El público aplaudió el último acto de la obra teatral.',
'El juego incluye niveles cooperativos y una campaña individual.'],
'miscelaneos':[
'Lista de pendientes: cambiar la bombilla, comprar jabón y ordenar el cajón.',
'Notas del hogar: revisar la llave de agua y limpiar el estante.',
'Recordatorio: llevar un paraguas, una libreta y una botella reutilizable.',
'Inventario personal: dos cajas, tres cables y una funda de tela.',
'Apunte rápido: preguntar por el horario del servicio de mensajería.',
'Lista para el fin de semana: lavar cortinas y organizar las herramientas.',
'Anotación doméstica: separar papel y vidrio para reciclaje.',
'Recados: recoger un paquete y comprar pilas para el control remoto.']}

def dump(path,obj):
    with path.open('x',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def png(seed):
    # PNG autentico, 32x32 RGB, patron abstracto NO foto ni evidencia semantica.
    r=random.Random(seed)
    pixels=b''.join(b'\x00'+bytes(r.randrange(256) for _ in range(32*3)) for _ in range(32))
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',32,32,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels,9))+chunk(b'IEND',b'')

def make(root,seed):
    if root.exists():raise SystemExit('ERROR: destino existente, no se sobrescribe')
    if root == Path.home() or root == Path('/') or root.is_symlink() or root.parent.is_symlink():raise SystemExit('ERROR: destino inseguro')
    root.mkdir(parents=True);(root/'dataset').mkdir();(root/'reference').mkdir()
    rng=random.Random(seed); records=[]
    for cat in CATS:
        for i,topic in enumerate(TOPICS[cat]):
            ident=f'doc_{rng.getrandbits(64):016x}'
            ext=('txt','md','csv','json')[i%4]
            if ext=='txt':content=topic+'\n'
            elif ext=='md':content='# Nota\n\n'+topic+'\n'
            elif ext=='csv':content='detalle\n"'+topic.replace('"','""')+'"\n'
            else:content=json.dumps({'detalle':topic},ensure_ascii=False)+'\n'
            name=f'{ident}.{ext}'; data=content.encode('utf-8');(root/'dataset'/name).write_bytes(data)
            records.append({'nombre':name,'categoria_esperada':cat,'formato':ext,'sha256':hashlib.sha256(data).hexdigest()})
    for cat in CATS:
        ident=f'img_{rng.getrandbits(64):016x}';name=ident+'.png';data=png(rng.getrandbits(64));(root/'dataset'/name).write_bytes(data)
        records.append({'nombre':name,'categoria_esperada':cat,'formato':'png','sha256':hashlib.sha256(data).hexdigest(),'advertencia':'patron_abstracto_sin_semantica'})
    rng.shuffle(records)
    dump(root/'reference'/'manifest.json',{'schema_version':1,'seed':seed,'advertencia':'Datos sinteticos escritos a mano, no prueba de generalizacion. PNG abstractos sin significado de categoria.','files':records})
    print('R5-L nuevo conjunto: 72 archivos (64 texto, 8 PNG abstractos).')
    print('Dataset:',root/'dataset');print('Referencia separada:',root/'reference'/'manifest.json')
    print('NO usar referencia como entrada de Qwen. No se ejecuta inferencia en este paso.')

def replay(lab):
    manifest=json.loads((lab/'reference'/'manifest.json').read_text())['files']
    truth={x['nombre']:x for x in manifest}
    with (lab/'baseline_predictions.csv').open(newline='',encoding='utf-8') as f:base=list(csv.DictReader(f))
    pilot=json.loads((lab/'r5_piloto.json').read_text())
    with (lab/'r5j_predictions.jsonl').open(encoding='utf-8') as f:rest=[json.loads(line) for line in f if line.strip()]
    predictions=pilot+rest
    if len(base)!=1000 or len(predictions)!=90 or len({x['nombre'] for x in predictions})!=90:raise SystemExit('ERROR: datos originales incompletos')
    byname={x['nombre']:x for x in predictions};original=Counter();policy=Counter()
    for b in base:
        name=b['nombre'];expected=truth[name]['categoria_esperada']
        if b['prediccion']!='ABSTENERSE':
            original['correcta' if b['prediccion']==expected else 'incorrecta']+=1
            policy['correcta' if b['prediccion']==expected else 'incorrecta']+=1
            continue
        p=byname[name];cat=p['categoria'] if p['json_valido'] else None
        original['abstencion' if cat is None else ('correcta' if cat==expected else 'incorrecta')]+=1
        # Politica candidata para prueba futura: sin vision, no clasificar PNG.
        if truth[name]['formato']=='png':cat=None
        policy['abstencion' if cat is None else ('correcta' if cat==expected else 'incorrecta')]+=1
    print('R5-L REPLAY RETROSPECTIVO (NO nuevo benchmark)')
    print('Hibrido original:',dict(original))
    print('Politica PNG -> abstencion:',dict(policy))
    print('ADVERTENCIA: politica elegida despues de ver errores; validacion independiente pendiente.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',type=Path,default=Path.home()/'pieza-lab-20261105');p.add_argument('--seed',type=int,default=20261106)
    sub=p.add_subparsers(dest='action',required=True);sub.add_parser('replay');sub.add_parser('generate')
    args=p.parse_args();lab=args.lab.expanduser().absolute()
    if args.action=='replay':replay(lab)
    else:make(lab.parent/f'pieza-lab-r5l-{args.seed}',args.seed)
if __name__=='__main__':main()
