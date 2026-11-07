import json, tempfile, unittest
from pathlib import Path
from pieza_por_pieza import vision
from pieza_por_pieza.organizador_final import plan, agrupar, execute, check_root

def jpeg_con_exif(path, fecha_original=None, fecha=None):
    """JPEG mínimo con EXIF armado a mano (sin Pillow)."""
    import struct
    entradas0, sub = [], b''
    datos_extra = b''
    def ascii_tag(tag, s, base):
        return struct.pack('<HHII', tag, 2, 20, base)
    tiff = bytearray(b'II*\x00' + struct.pack('<I', 8))
    tags0 = []
    if fecha: tags0.append((0x0132, fecha))
    n0 = len(tags0) + (1 if fecha_original else 0)
    ifd0_size = 2 + n0 * 12 + 4
    pos = 8 + ifd0_size
    cuerpo0, valores = b'', b''
    for tag, s in tags0:
        cuerpo0 += struct.pack('<HHII', tag, 2, 20, pos + len(valores)); valores += s.encode() + b'\x00'
    exif_off = pos + len(valores)
    if fecha_original:
        cuerpo0 += struct.pack('<HHII', 0x8769, 4, 1, exif_off)
        sub_val_pos = exif_off + 2 + 12 + 4
        sub = struct.pack('<H', 1) + struct.pack('<HHII', 0x9003, 2, 20, sub_val_pos) + b'\x00' * 4 + fecha_original.encode() + b'\x00'
    tiff += struct.pack('<H', n0) + cuerpo0 + b'\x00' * 4 + valores + sub
    app1 = b'Exif\x00\x00' + bytes(tiff)
    Path(path).write_bytes(b'\xff\xd8' + b'\xff\xe1' + struct.pack('>H', len(app1) + 2) + app1 + b'\xff\xd9')

class Vision(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.base = Path(t.name); self.src = self.base / 'fotos'; self.src.mkdir()
    def test_exif_original_y_respaldo(self):
        jpeg_con_exif(self.src / 'a.jpg', fecha_original='2019:07:14 18:30:00', fecha='2023:01:01 00:00:00')
        jpeg_con_exif(self.src / 'b.jpg', fecha='2021:12:24 20:00:00')
        (self.src / 'c.jpg').write_bytes(b'\xff\xd8\xff\xd9')
        (self.src / 'roto.jpg').write_bytes(b'\xff\xd8\xff\xe1\x00')
        self.assertEqual(vision.fecha_exif(self.src / 'a.jpg'), '2019/2019-07')
        self.assertEqual(vision.fecha_exif(self.src / 'b.jpg'), '2021/2021-12')
        self.assertIsNone(vision.fecha_exif(self.src / 'c.jpg'))
        self.assertIsNone(vision.fecha_exif(self.src / 'roto.jpg'))
    def test_criterio_fecha_foto(self):
        jpeg_con_exif(self.src / 'IMG_1.jpg', fecha_original='2019:07:14 18:30:00')
        rows, _, _ = plan(self.src)
        info = agrupar(rows, 'fecha_foto', root=self.src)
        self.assertEqual(rows[0]['grupo'], '2019/2019-07')
        self.assertEqual(info['con_fecha_camara'], 1)
    def test_criterio_contenido_con_qwen_falso(self):
        for n, f in (('IMG_1.jpg', '2020:01:01 00:00:00'), ('IMG_2.jpg', '2021:02:02 00:00:00')):
            jpeg_con_exif(self.src / n, fecha=f)
        (self.src / 'notas.txt').write_text('lista de jugadores')
        rows, sk, tot = plan(self.src)
        vistos = iter(['futbolista celebrando', 'playa al atardecer'])
        from pieza_por_pieza.organizador_final import huellas
        huellas(self.src, rows)
        original = vision.miniatura; vision.miniatura = lambda p, h: b'\xff\xd8x'
        self.addCleanup(setattr, vision, 'miniatura', original)
        res = vision.describir_todo(check_root(self.src), rows, consultar=lambda jpeg: next(vistos), herramienta='pillow')
        self.assertEqual(res['descritas'], 2)
        textos = []
        def qwen(system, user, m):
            textos.append(user)
            if 'INICIO NOMBRE NO CONFIABLE\n' in user:
                l = user.split('INICIO NOMBRE NO CONFIABLE\n')[1]
                return json.dumps({'proyecto': 1 if 'futbol' in l.split('\nFIN')[0] else 2 if 'playa' in l.split('\nFIN')[0] else 0})
            if 'asignaciones' in user:
                body = user.split('INICIO NOMBRES NO CONFIABLES\n')[1].split('\nFIN')[0]
                return json.dumps({'asignaciones': {l.split('. ')[0]: (1 if 'futbol' in l else 2 if 'playa' in l else 0) for l in body.splitlines()}})
            return '{"proyectos":["Futbol","Playa"]}'
        agrupar(rows, 'contenido_ia', consultar=qwen)
        self.assertIn('se ve: futbolista celebrando', textos[0])
        g = {r['ruta_relativa']: r['grupo'] for r in rows}
        self.assertEqual((g['IMG_1.jpg'], g['IMG_2.jpg'], g['notas.txt']), ('Futbol', 'Playa', 'Otros'))
        out = self.base / 'salida'
        execute(self.src, out, 'personal', rows, sk, tot)
        m = json.loads((out / 'MANIFIESTO_PRIVADO.json').read_text())
        self.assertIn('futbolista celebrando', {e.get('qwen_vio') for e in m['archivos']})
    def test_sin_vision_se_detiene(self):
        jpeg_con_exif(self.src / 'x.jpg')
        rows, _, _ = plan(self.src)
        def falla(jpeg): raise ValueError('SIN_VISION')
        original = vision.miniatura; vision.miniatura = lambda p, h: b'\xff\xd8x'
        self.addCleanup(setattr, vision, 'miniatura', original)
        with self.assertRaisesRegex(ValueError, 'sin visión|SIN visión|no tiene visión'):
            vision.describir_todo(check_root(self.src), rows, consultar=falla, herramienta='pillow')
    def test_limpiar_descripcion(self):
        self.assertEqual(vision.limpiar('  hola\n{"x": [1]}  `rm` '), 'hola "x": 1 rm')
        self.assertLessEqual(len(vision.limpiar('a' * 500)), 100)

    def test_servidor_recibe_mmproj(self):
        import os, sys, time
        from unittest.mock import patch
        from pieza_por_pieza.servidor import Gestor
        exe = self.base / 'llama-server'; exe.write_text('#!' + sys.executable + '\nimport sys; print(" ".join(sys.argv[1:]))\n'); exe.chmod(0o755)
        (self.base / 'm.gguf').write_bytes(b'x'); (self.base / 'mmproj-F16.gguf').write_bytes(b'x')
        g = Gestor()
        with patch.object(g, 'puerto_ocupado', return_value=False):
            g.iniciar(str(exe), str(self.base / 'm.gguf'), mmproj=self.base / 'mmproj-F16.gguf')
        g.proceso.wait(10); g.registro.flush(); time.sleep(.1)
        self.assertIn('--mmproj', g.ruta_registro.read_text()); self.assertTrue(g.vision)
        g.detener(); g.ruta_registro.unlink()

if __name__ == '__main__': unittest.main()

class AsignacionRobusta(unittest.TestCase):
    def test_duplicados_van_juntos_y_se_miran_una_vez(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); src = Path(t.name) / 'f'
        (src / 'Nueva carpeta').mkdir(parents=True)
        jpeg_con_exif(src / 'IMG_1.jpg', fecha='2020:01:01 00:00:00')
        (src / 'Nueva carpeta' / 'IMG_1.jpg').write_bytes((src / 'IMG_1.jpg').read_bytes())
        jpeg_con_exif(src / 'IMG_9.jpg', fecha='2022:01:01 00:00:00')
        rows, _, _ = plan(src)
        from pieza_por_pieza.organizador_final import huellas
        huellas(src, rows)
        original = vision.miniatura; vision.miniatura = lambda p, h: b'\xff\xd8x'
        self.addCleanup(setattr, vision, 'miniatura', original)
        mirados = []
        def ver(jpeg): mirados.append(1); return 'playa' if len(mirados) == 1 else 'montaña'
        vision.describir_todo(check_root(src), rows, consultar=ver, herramienta='pillow')
        self.assertEqual(len(mirados), 2)                     # 3 fotos, 2 distintas
        preguntas = []
        def qwen(s, u, m):
            if 'Grupos disponibles' not in u: return '{"proyectos":["Playa","Montaña"]}'
            preguntas.append(u); return '{"proyecto": %d}' % (1 if 'playa' in u.split('INICIO NOMBRE')[1] else 2)
        info = agrupar(rows, 'contenido_ia', consultar=qwen, root=src)
        g = {r['ruta_relativa']: r['grupo'] for r in rows}
        self.assertEqual(g['IMG_1.jpg'], g['Nueva carpeta/IMG_1.jpg'])
        self.assertEqual((g['IMG_1.jpg'], g['IMG_9.jpg']), ('Playa', 'Montaña'))
        self.assertEqual((len(preguntas), info['consultados']), (2, 2))
    def test_respuesta_por_nombre_o_texto(self):
        from pieza_por_pieza.agrupador import _elegido
        P = ['Playa', 'Montaña']
        self.assertEqual([_elegido(v, P) for v in (1, '2', 'Montaña', 'montaña', 3, True, None, 'Luna')],
                         ['Playa', 'Montaña', 'Montaña', 'Montaña', None, None, None, None])
