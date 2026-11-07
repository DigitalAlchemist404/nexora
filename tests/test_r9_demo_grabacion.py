import io, subprocess, sys, tempfile, unittest
from pathlib import Path
from pieza_por_pieza import cli
from pieza_por_pieza.clasificador_local import safe_path
from pieza_por_pieza.organizador_final import plan
from pieza_por_pieza.vision import fecha_exif

DEMO = Path(__file__).resolve().parent.parent / 'demo' / 'crear_carpeta_demo.py'

class CarpetaDemo(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.base = Path(t.name)
    def correr(self, *args):
        return subprocess.run([sys.executable, str(DEMO), *args], capture_output=True, text=True)
    def test_crea_borra_y_protege(self):
        destino = self.base / 'NEXORA_DEMO'
        r = self.correr('--destino', str(destino)); self.assertEqual(r.returncode, 0, r.stderr)
        raiz = destino / 'Descargas_demo'
        self.assertEqual(fecha_exif(raiz / 'IMG_2041.jpg'), '2024/2024-07')
        omitidos = []; rows, sk, _ = plan(raiz, omitidos=omitidos)
        self.assertIn(('contraseñas_wifi.txt', 'nombre sensible: no se lee ni se copia'), omitidos)
        self.assertGreater(len(rows), 60)
        self.assertNotEqual(self.correr('--destino', str(destino)).returncode, 0)   # ya existe
        self.assertEqual(self.correr('--destino', str(destino), '--borrar').returncode, 0)
        self.assertFalse(destino.exists())
    def test_no_usa_carpetas_ajenas(self):
        ajena = self.base / 'Descargas'; ajena.mkdir(); (ajena / 'mio.txt').write_text('mío')
        self.assertNotEqual(self.correr('--destino', str(ajena)).returncode, 0)
        self.assertNotEqual(self.correr('--destino', str(ajena), '--borrar').returncode, 0)
        self.assertTrue((ajena / 'mio.txt').exists())

class Privacidad(unittest.TestCase):
    def test_nombres_sensibles_en_espanol(self):
        for n in ('contraseñas_wifi.txt', 'Contrasenas.txt', 'mis_secretos/notas.md', 'pasaporte.jpg', 'cédula_frente.png'):
            self.assertFalse(safe_path(n), n)
        self.assertTrue(safe_path('receta_pizza.txt'))
    def test_modo_grabacion_oculta_rutas(self):
        salida = io.StringIO(); g = cli._Grabacion(salida)
        g.write(f'Salida: {Path.home()}/NEXORA_DEMO/x\n')
        import getpass; u = getpass.getuser()
        g.write(f'/media/{u}/disco/@home/{u}/modelo.gguf\n')
        texto = salida.getvalue()
        self.assertIn('~/NEXORA_DEMO/x', texto); self.assertNotIn(str(Path.home()), texto)
        if len(u) >= 2: self.assertNotIn(f'/{u}/', texto)

if __name__ == '__main__': unittest.main()
