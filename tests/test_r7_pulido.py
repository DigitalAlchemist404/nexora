import tempfile, unittest
from pathlib import Path
from pieza_por_pieza.organizador_final import plan, check_root, _destino

class Pulido(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.base = Path(t.name)
    def test_mensajes_de_origen_claros(self):
        with self.assertRaisesRegex(ValueError, 'No existe'): check_root(self.base / 'nada')
        (self.base / 'modelo.gguf').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError, 'archivo, no una carpeta'): check_root(self.base / 'modelo.gguf')
        (self.base / 'c').mkdir()
        self.assertEqual(check_root(f'"{self.base / "c"}" '), (self.base / 'c').resolve())  # comillas/espacios al pegar
    def test_pista_de_conflicto_ignora_carpetas_genericas(self):
        used = set()
        r1 = {'ruta_relativa': 'video_cumple/assets/musica.m4a', 'categoria': 'audio'}
        r2 = {'ruta_relativa': 'videos/viajes/video_playa/assets/musica.m4a', 'categoria': 'audio'}
        _destino(r1, 'personal', used)
        _, nombre = _destino(r2, 'personal', used)
        self.assertEqual(nombre, 'musica__video_playa.m4a')
    def test_pycache_omitido_y_motivo_en_revisar(self):
        src = self.base / 'src'; (src / '__pycache__').mkdir(parents=True)
        (src / '__pycache__' / 'x.cpython-312.pyc').write_bytes(b'\x00')
        (src / 'raro.xyz').write_bytes(b'?')
        (src / 'LEEME.txt').write_text('ejecutá python3 render.py')
        rows, skipped, _ = plan(src, use_ai=True, classifier=lambda d: ('codigo', 'alta'))
        nombres = {Path(r['ruta_relativa']).name: r for r in rows}
        self.assertNotIn('x.cpython-312.pyc', nombres)
        self.assertEqual(nombres['raro.xyz']['motivo'], 'Tipo de archivo desconocido')
        self.assertIn("Qwen dijo 'codigo'", nombres['LEEME.txt']['motivo'])

if __name__ == '__main__': unittest.main()
