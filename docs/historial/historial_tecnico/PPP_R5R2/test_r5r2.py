#!/usr/bin/env python3
"""Pruebas destructivas SOLO sobre laboratorios temporales creados por este archivo."""
import hashlib, json, pathlib, subprocess, sys, tempfile, unittest

SCRIPT = pathlib.Path(__file__).with_name('r5r.py').resolve()

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ppp-r5r2-')
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / 'demo'
        self.call('prepare')
        self.call('plan')
        self.plan = json.loads((self.root/'state'/'plan.json').read_text())

    def call(self, command, *extra, ok=True):
        p = subprocess.run([sys.executable, str(SCRIPT), command, '--root', str(self.root), *extra], capture_output=True, text=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def authorize(self):
        self.call('approve', '--digest', self.plan['plan_sha256'], '--confirm', 'AUTORIZO DEMO R5R')

    def test_no_authorization(self):
        self.call('execute', ok=False)
        self.call('verify')
        self.assertEqual(len(list((self.root/'inbox').glob('*.txt'))), 30)

    def test_wrong_digest(self):
        self.call('approve', '--digest', '0'*64, '--confirm', 'AUTORIZO DEMO R5R', ok=False)
        self.assertFalse((self.root/'state'/'approval.json').exists())

    def test_modified_source_hash(self):
        self.authorize()
        (self.root/'inbox'/'doc_001.txt').write_text('alterado')
        self.call('execute', ok=False)
        self.assertFalse((self.root/'sorted'/'universidad'/'doc_001.txt').exists())

    def test_collision(self):
        self.authorize()
        dst=self.root/'sorted'/'universidad'
        dst.mkdir()
        (dst/'doc_001.txt').write_text('ocupado')
        self.call('execute', ok=False)
        self.assertEqual((dst/'doc_001.txt').read_text(), 'ocupado')
        self.assertTrue((self.root/'inbox'/'doc_001.txt').exists())

    def test_symlink_destination(self):
        self.authorize()
        external=pathlib.Path(self.temp.name)/'external'
        external.mkdir()
        (self.root/'sorted'/'universidad').symlink_to(external, target_is_directory=True)
        self.call('execute', ok=False)
        self.assertEqual(list(external.iterdir()), [])

    def test_tampered_plan_traversal(self):
        planfile=self.root/'state'/'plan.json'
        p=json.loads(planfile.read_text())
        p['actions'][0]['destination']='../outside/doc_001.txt'
        p.pop('plan_sha256')
        p['plan_sha256']=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        planfile.write_text(json.dumps(p))
        self.call('execute',ok=False)
        self.assertFalse((pathlib.Path(self.temp.name)/'outside').exists())

    def test_idempotence_and_rollback(self):
        self.authorize()
        self.call('execute')
        self.assertIn('0 movimientos nuevos',self.call('execute').stdout)
        self.call('verify')
        self.call('rollback')
        self.assertIn('0 movimientos',self.call('rollback').stdout)
        self.call('verify')
        self.assertEqual(len(list((self.root/'inbox').glob('*.txt'))),30)

    def test_resume_after_partial_progress(self):
        self.authorize()
        a=self.plan['actions'][0]
        src=self.root/a['source'];dst=self.root/a['destination']
        dst.parent.mkdir(parents=True,exist_ok=True)
        src.rename(dst)  # Simula movimiento completado antes de registrar evento
        self.call('execute')
        self.call('verify')
        self.assertEqual(len(list((self.root/'inbox').glob('*.txt'))),0)
        self.call('rollback')
        self.call('verify')

if __name__=='__main__':
    unittest.main(verbosity=2)
