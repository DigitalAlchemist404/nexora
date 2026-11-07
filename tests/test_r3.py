import unittest
from pathlib import Path
from pieza_por_pieza import clasificador_local
class TestR3(unittest.TestCase):
    def test_baseline(self):
        self.assertEqual(clasificador_local.baseline('.py'),'codigo')
        self.assertEqual(clasificador_local.baseline('.md'),'documento')
    def test_safety(self):
        self.assertFalse(clasificador_local.safe_path('secret/abc.py'))
        self.assertTrue(clasificador_local.safe_path('ejemplo.py'))
if __name__=='__main__': unittest.main()
