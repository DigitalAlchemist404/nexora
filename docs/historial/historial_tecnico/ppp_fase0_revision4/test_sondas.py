import contextlib
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sondas as a

class Handler(http.server.BaseHTTPRequestHandler):
    enforce = True
    def log_message(self, *args):
        pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        value = 'PROMPT'
        if self.enforce and 'response_format' in body:
            value = body['response_format']['json_schema']['schema']['properties']['marca']['enum'][0]
        data = json.dumps({'choices': [{'message': {'content': json.dumps({'marca': value})},
                                       'finish_reason': 'stop'}], 'usage': {}}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(data)

class Tests(unittest.TestCase):
    def test_strict_json(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', "'{\"a\":1}'", 'texto {}'):
            with self.assertRaises(ValueError):
                a.strict_loads(text)
        self.assertEqual(a.strict_loads(' {"a":1} '), {'a': 1})
    def test_batch_contract(self):
        valid = {'archivos': [{'id': 'f000', 'categoria': 'Revision'}, {'id': 'f001', 'categoria': 'Universidad'}]}
        self.assertTrue(a.check_batch(valid, 2))
        valid['archivos'][1]['id'] = 'f000'
        self.assertFalse(a.check_batch(valid, 2))
        self.assertFalse(a.check_batch({'archivos': []}, 2))
        self.assertFalse(a.check_batch({'archivos': [{'id': 'f000', 'categoria': 'X'}]}, 1))
    def contrast(self, enforce):
        handler = type('MockHandler', (Handler,), {'enforce': enforce})
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with contextlib.redirect_stdout(None):
                    rows, verdict = a.run_contrast(a.Client(server.server_port), Path(tmp))
                self.assertEqual(len(rows), 4)
                self.assertEqual(len(list(Path(tmp).glob('*json'))), 8)
                return verdict
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    def test_server_honors_schema(self):
        self.assertEqual(self.contrast(True), 'EVIDENCIA_POSITIVA_EN_DOS_CONTRASTES')
    def test_server_ignores_schema(self):
        self.assertEqual(self.contrast(False), 'INCONCLUSO_O_FALLIDO')
    def test_no_redirect(self):
        self.assertIsNone(a.NoRedirect().redirect_request())

if __name__ == '__main__':
    unittest.main()
