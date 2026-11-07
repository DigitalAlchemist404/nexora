import json, tempfile, unittest
from pathlib import Path
from pieza_por_pieza.organizador_final import plan, run

class Correcciones(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.src=Path(t.name)/'descargas';(self.src/'playa').mkdir(parents=True);(self.src/'cumple').mkdir()
        (self.src/'playa'/'foto.jpg').write_bytes(b'\xff\xd8JPEG1')
        (self.src/'cumple'/'foto.jpg').write_bytes(b'\xff\xd8JPEG1')   # duplicado exacto
        (self.src/'cumple'/'clip.mp4').write_bytes(b'MP4')
        (self.src/'fuente.ttf').write_bytes(b'TTF')
        (self.src/'playa'/'LEEME.txt').write_text('notas playa')
        (self.src/'cumple'/'LEEME.txt').write_text('notas cumple')
    def test_multimedia_por_extension_en_ambos_modos(self):
        for ai in (False,True):
            rows,_,_=plan(self.src,use_ai=ai,classifier=lambda d:('documento','media'))
            cats={r['ruta_relativa']:r['categoria'] for r in rows}
            self.assertEqual(cats['cumple/clip.mp4'],'video')
            self.assertEqual(cats['fuente.ttf'],'fuente')
            self.assertEqual(cats['playa/foto.jpg'],'imagen')
            self.assertEqual(cats['playa/LEEME.txt'],'documento')  # IA media + coincide extensión
    def test_ia_baja_confianza_a_revisar(self):
        rows,_,_=plan(self.src,use_ai=True,classifier=lambda d:('documento','baja'))
        self.assertEqual({r['categoria'] for r in rows if r['ruta_relativa'].endswith('.txt')},{'revisar'})
    def test_duplicados_y_nombres_con_carpeta(self):
        out,summary=run(self.src,'personal')
        org=out/'ORGANIZADOS'
        self.assertEqual(summary['duplicados_exactos_no_copiados'],1)
        self.assertEqual(len(list((org/'Imagenes').iterdir())),1)
        self.assertTrue((org/'Documentos'/'LEEME.txt').exists())
        self.assertTrue((org/'Documentos'/'LEEME__playa.txt').exists())
        m=json.loads((out/'MANIFIESTO_PRIVADO.json').read_text())
        self.assertEqual(m['duplicados'][0]['origen_relativo'],'playa/foto.jpg')
        self.assertTrue((self.src/'cumple'/'foto.jpg').exists())  # origen intacto

if __name__=='__main__':unittest.main()
