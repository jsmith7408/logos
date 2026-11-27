import unittest, tempfile, os, io, json
from pathlib import Path
from contextlib import redirect_stdout
from runtime31 import keyfile, main

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.key=Path(t.name)/'key'; self.db=Path(t.name)/'db'
    def test_key(self):
        keyfile(self.key,True); self.assertEqual(len(keyfile(self.key)),32)
        with self.assertRaises(FileExistsError): keyfile(self.key,True)
    def test_permissions(self):
        keyfile(self.key,True); os.chmod(self.key,0o644)
        with self.assertRaises(ValueError): keyfile(self.key)
    def test_symlink(self):
        keyfile(self.key,True); link=self.key.with_name('link'); link.symlink_to(self.key)
        with self.assertRaises(OSError): keyfile(link)
    def test_cli(self):
        args=['--key',str(self.key),'--db',str(self.db)]
        def call(*cmd):
            with redirect_stdout(io.StringIO()) as out: main(args+list(cmd))
            return json.loads(out.getvalue())
        call('init'); r=call('solve','A is 5; find A')
        self.assertEqual(r['result']['answer'],'5'); self.assertEqual(r,call('retrieve',r['id']))
        self.assertEqual(r['evidence_status'],'unverified')
