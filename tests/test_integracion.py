import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pieza_por_pieza.servidor import Gestor
from pieza_por_pieza import modelos

class TestIntegracion(unittest.TestCase):
    def test_gguf_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'blob').write_bytes(b'x'*1024)
            (p/'modelo.gguf').symlink_to('blob')
            models,limited=modelos.scan([p])
            self.assertFalse(limited)
            self.assertEqual([m.name for m in models],['modelo.gguf'])
    def test_filter(self):
        self.assertEqual(modelos.category(Path('ggml-vocab-qwen35.gguf')),'auxiliar')
        self.assertEqual(modelos.category(Path('Wan2.2-TI2V.gguf')),'especializado')
    def test_no_start_when_port_occupied(self):
        m=Gestor()
        with patch.object(m,'puerto_ocupado',return_value=True):
            with self.assertRaises(RuntimeError):m.iniciar('/no/exe','/no/model')
        self.assertIsNone(m.proceso)
    def test_no_stop_external(self):
        m=Gestor();self.assertFalse(m.detener())

if __name__=='__main__':unittest.main()
