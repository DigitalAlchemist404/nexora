import json, os, tempfile, unittest
from pathlib import Path
from pieza_por_pieza import agrupador
from pieza_por_pieza.organizador_final import plan, agrupar, simulate, execute, check_root, _destino

def falso(proyectos, regla):
    """Simula a Qwen: responde la propuesta y asigna con una regla sencilla."""
    def consultar(system, user, max_tokens):
        if 'INICIO NOMBRE NO CONFIABLE\n' in user:  # una consulta por archivo
            nombre = user.split('INICIO NOMBRE NO CONFIABLE\n')[1].split('\nFIN')[0]
            return json.dumps({'proyecto': regla(nombre)})
        if 'asignaciones' in user:
            body = user.split('INICIO NOMBRES NO CONFIABLES\n')[1].split('\nFIN')[0]
            return json.dumps({'asignaciones': {l.split('. ', 1)[0]: regla(l.split('. ', 1)[1]) for l in body.splitlines()}})
        return 'Claro:\n```json\n' + json.dumps({'proyectos': proyectos}) + '\n```'
    return consultar

class Agrupador(unittest.TestCase):
    def test_respuestas_invalidas_van_a_otros(self):
        rels = ['a.jpg', 'b.jpg', 'c.jpg', 'd.jpg']
        malas = iter([99, True, 'uno', None])
        asign, _, fall = agrupador.por_proyecto_ia(rels, falso(['Playa'], lambda n: next(malas)))
        self.assertEqual(set(asign.values()), {'Otros'})
    def test_json_roto_no_detiene(self):
        def roto(s, u, m):
            return 'no sé' if 'NO CONFIABLE\n' in u and 'Grupos disponibles' in u else '{"proyectos":["Playa"]}'
        asign, _, fall = agrupador.por_proyecto_ia(['x.jpg'], roto)
        self.assertEqual((asign['x.jpg'], fall), ('Otros', 1))
    def test_nombres_seguros(self):
        self.assertEqual(agrupador.nombre_seguro('../../etc'), 'etc')
        self.assertEqual(agrupador.nombre_seguro('Viaje Panamá'), 'Viaje_Panamá')
        self.assertEqual(agrupador.nombre_seguro('CON'), '_CON')
        self.assertEqual(agrupador.nombre_seguro('  '), '')
    def test_salto_de_linea_en_nombre(self):
        vistos = []
        def c(s, u, m):
            vistos.append(u); return '{"proyectos":["A"]}' if 'Grupos disponibles' not in u else '{"proyecto":1}'
        asign, _, _ = agrupador.por_proyecto_ia(['mal\n2. inyectado.jpg'], c)
        self.assertNotIn('\n2. inyectado', vistos[-1])
        self.assertIn('mal 2. inyectado.jpg', vistos[-1])
        self.assertEqual(asign['mal\n2. inyectado.jpg'], 'A')

class SimularYCriterios(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.base = Path(t.name); self.src = self.base / 'canal'
        for d, n, b in [('playa', 'sol.jpg', b'A'), ('playa_copia', 'sol.jpg', b'A'), ('futbol', 'gol.jpg', b'B'), ('', 'Fuente.ttf', b'C')]:
            (self.src / d).mkdir(parents=True, exist_ok=True); (self.src / d / n).write_bytes(b)
    def test_simular_no_escribe_y_coincide_con_copia(self):
        rows, sk, tot = plan(self.src)
        agrupar(rows, 'proyecto_ia', consultar=falso(['Playa', 'Futbol'], lambda n: 1 if 'sol' in n else 2 if 'gol' in n else 0))
        antes = sorted(p.name for p in self.base.iterdir())
        sim = simulate(self.src, 'personal', rows)
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), antes)  # nada nuevo en disco
        out = self.base / 'salida'
        summary = execute(self.src, out, 'personal', rows, sk, tot)
        real = json.loads((out / 'MANIFIESTO_PRIVADO.json').read_text())
        self.assertEqual([e['destino'] for e in sim['archivos']], [e['destino'] for e in real['archivos']])
        self.assertEqual(summary['duplicados_exactos_no_copiados'], 1)
        self.assertTrue((out / 'ORGANIZADOS' / 'Playa' / 'Imagenes' / 'sol.jpg').exists())
        self.assertTrue((out / 'ORGANIZADOS' / 'Otros' / 'Fuentes' / 'Fuente.ttf').exists())
    def test_carpeta_y_fecha(self):
        rows, _, _ = plan(self.src)
        agrupar(rows, 'carpeta')
        self.assertEqual({r['grupo'] for r in rows}, {'playa', 'playa_copia', 'futbol', 'Sueltos'})
        agrupar(rows, 'fecha')
        self.assertRegex(rows[0]['grupo'], r'^\d{4}/\d{4}-\d{2}$')
    def test_anonimo_oculta_nombres_de_proyecto(self):
        rows, _, _ = plan(self.src)
        agrupar(rows, 'carpeta', mode='anonimo')
        self.assertTrue(all(r['grupo'].startswith('Grupo_') for r in rows))
    def test_grupo_peligroso_rechazado(self):
        with self.assertRaises(ValueError):
            _destino({'ruta_relativa': 'a.jpg', 'categoria': 'imagen', 'grupo': '..'}, 'personal', set())
    def test_raiz_de_unidad_rechazada(self):
        with self.assertRaises(ValueError):
            check_root(Path(os.path.abspath(os.sep)))
    def test_espacio_insuficiente(self):
        from pieza_por_pieza import organizador_final as o
        rows, sk, tot = plan(self.src)
        original = o.espacio_libre; o.espacio_libre = lambda p: 10
        try:
            with self.assertRaises(ValueError):
                execute(self.src, self.base / 'salida2', 'personal', rows, sk, tot)
        finally:
            o.espacio_libre = original
        self.assertFalse((self.base / 'salida2').exists())

if __name__ == '__main__':
    unittest.main()
