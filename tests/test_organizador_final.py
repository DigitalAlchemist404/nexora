import json
from pathlib import Path
import tempfile
import unittest
from pieza_por_pieza.organizador_final import run, plan, execute

class OrganizadorFinal(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.source=self.base/'origen'
        self.source.mkdir()
        (self.source/'programa.py').write_text('print(42)')
        (self.source/'notas.md').write_text('Notas del proyecto')
        (self.source/'otro').mkdir()
        (self.source/'otro'/'programa.py').write_text('print(123)')
        (self.source/'.env').write_text('SECRETO=abc')
    def test_personal_names_collision_hashes(self):
        out,summary=run(self.source,'personal')
        self.assertEqual(summary['archivos_copiados'],3)
        self.assertTrue((out/'ORGANIZADOS'/'Codigo'/'programa.py').exists())
        self.assertTrue((out/'ORGANIZADOS'/'Codigo'/'programa__otro.py').exists())
        self.assertTrue((out/'ORGANIZADOS'/'Documentos'/'notas.md').exists())
        self.assertFalse((out/'ORGANIZADOS'/'Documentos'/'.env').exists())
        self.assertEqual((self.source/'programa.py').read_text(),'print(42)')
        m=json.loads((out/'MANIFIESTO_PRIVADO.json').read_text())
        self.assertEqual(len(m['archivos']),3)
    def test_anon_names_no_original_in_manifest(self):
        out,summary=run(self.source,'anonimo')
        self.assertEqual(summary['archivos_copiados'],3)
        self.assertNotIn('programa.py',(out/'MANIFIESTO_PRIVADO.json').read_text())
        self.assertFalse((out/'ORGANIZADOS'/'Codigo'/'programa.py').exists())
    def test_reject_output_inside_source(self):
        rows,skipped,total=plan(self.source)
        with self.assertRaises(ValueError):
            execute(self.source,self.source/'salida','personal',rows,skipped,total)
    def test_no_overwrite(self):
        out,_=run(self.source,'personal')
        rows,skipped,total=plan(self.source)
        with self.assertRaises(FileExistsError):
            execute(self.source,out,'personal',rows,skipped,total)
    def test_ai_disagreement_to_review(self):
        rows,_,_=plan(self.source,use_ai=True,classifier=lambda data:('codigo','alta'))
        doc=[r for r in rows if r['ruta_relativa']=='notas.md'][0]
        self.assertEqual(doc['categoria'],'revisar')
    def test_symlink_skipped(self):
        (self.source/'link.py').symlink_to(self.source/'programa.py')
        rows,skipped,_=plan(self.source)
        self.assertEqual(len(rows),3)
        self.assertGreaterEqual(skipped,1)

if __name__=='__main__':unittest.main()
