import unittest
from pathlib import Path
from pieza_por_pieza import cli

class Integracion(unittest.TestCase):
 def test_script_auditoria_existe(self):
  self.assertTrue(Path(cli.__file__).with_name('auditoria_copias.py').is_file())
 def test_menu_expuesto(self):
  self.assertTrue(callable(cli.auditoria_copias))
