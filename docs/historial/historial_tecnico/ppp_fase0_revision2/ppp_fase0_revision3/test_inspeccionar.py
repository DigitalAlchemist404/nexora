import unittest
import inspeccionar as a

class Tests(unittest.TestCase):
    def test_help_boundaries(self):
        text = '--reasoning [on|off]\n  Explanation.\n--unrelated PATH\n secret\n--reasoning-budget N\n  Budget.'
        result = a.help_blocks(text)
        self.assertEqual(set(result), {'--reasoning', '--reasoning-budget'})
        self.assertNotIn('secret', str(result))
        self.assertIn('Explanation', result['--reasoning'])
    def test_redaction(self):
        text = 'File /home/someone/secret; mail person@example.test https://example.test/x'
        result = a.clean(text)
        self.assertNotIn('/home', result)
        self.assertNotIn('person@', result)
        self.assertNotIn('example.test', result)
    def test_socket_match(self):
        text = 'header\n 0: 0100007F:1F90 00000000:0000 0A 0 0 0 1000 0 456\n 1: 00000000:1F90 00000000:0000 0A 0 0 0 1000 0 789'
        self.assertEqual(a.listener_inodes(text), {'456'})
    def test_image_allowlist(self):
        result = a.safe_image({'Architecture': 'arm64', 'Os': 'linux', 'Config': {
            'Cmd': ['/usr/bin/python3', '/private/program.py'], 'Env': ['TOKEN=secret'],
            'Entrypoint': ['/private/entrypoint'], 'Volumes': {'/private': {}}}})
        self.assertEqual(result['interpretes_mencionados_en_config'], ['python3'])
        self.assertNotIn('secret', str(result))
        self.assertNotIn('/private', str(result))
        self.assertFalse(result['ejecutada'])

if __name__ == '__main__':
    unittest.main()
