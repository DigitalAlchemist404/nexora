import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import comparar as c

class Tests(unittest.TestCase):
    def test_only_reasoning_changes(self):
        original=['/example/llama-server','--model','/example/model.gguf','--host','127.0.0.1','--port','8080','--ctx-size','8192','--n-gpu-layers','99','--parallel','1']
        self.assertEqual(c.off_argv(original),original+['--reasoning','off'])
        self.assertEqual(c.off_argv(original+['--reasoning','on']),original+['--reasoning','off'])
    def test_unknown_or_secret_options_rejected(self):
        for argv in (['server','--api-key','secret'], ['server','--model'], ['server','--port','8080','--port','8081']):
            with self.assertRaises(c.CheckError):
                c.parse_args(argv)
    def test_environment(self):
        with patch.dict(c.os.environ,{'LLAMA_ARG_REASONING':'on','CUDA_VISIBLE_DEVICES':'wrong'},clear=True):
            env=c.child_env({'env':{'CUDA_VISIBLE_DEVICES':'0'}})
        self.assertNotIn('LLAMA_ARG_REASONING',env)
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'0')
    def test_report_comparability_and_no_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for mode,sec,sha in [('actual',20,'same'),('off',10,'same')]:
                (p/(mode+'.json')).write_text(json.dumps([{'archivos':5,'completo':True,'segundos':sec,'solicitud_sha256':sha}]))
            report=c.public_report(p)
            self.assertEqual(report['comparaciones'][0]['factor_tiempo_actual_sobre_off'],2)
            self.assertNotIn(tmp,json.dumps(report))
            (p/'off.json').write_text(json.dumps([{'archivos':5,'completo':True,'segundos':10,'solicitud_sha256':'different'}]))
            self.assertNotIn('factor_tiempo_actual_sobre_off',c.public_report(p)['comparaciones'][0])
    def test_stop_only_passed_child(self):
        from unittest.mock import Mock
        child=Mock()
        child.poll.return_value=None
        c.stop_child(child)
        child.terminate.assert_called_once()
        child.wait.assert_called_once_with(timeout=20)
        child.kill.assert_not_called()

if __name__=='__main__':
    unittest.main()
