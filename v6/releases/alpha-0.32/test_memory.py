import unittest,tempfile,sqlite3
from pathlib import Path
from contextlib import closing
from memory import Memory,IntegrityError
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'db'; self.key=b'x'*32; self.m=Memory(self.path,self.key)
    def test_restart(self):
        r=self.m.append('claim','source'); self.assertEqual(Memory(self.path,self.key).get(r['id']),r)
    def test_tamper(self):
        r=self.m.append('claim','source')
        with closing(sqlite3.connect(self.path)) as db,db: db.execute("UPDATE memory SET payload='{}'")
        with self.assertRaises(IntegrityError): self.m.get(r['id'])
    def test_wrong_key(self):
        r=self.m.append('claim','source')
        with self.assertRaises(IntegrityError): Memory(self.path,b'y'*32).get(r['id'])
    def test_dependency(self):
        r=self.m.append('a','s'); t=self.m.append('b','s',[r['id']]); self.assertEqual(t['dependencies'],[r['id']])
    def test_missing(self):
        with self.assertRaises(KeyError): self.m.append('a','s',['missing'])
        with closing(sqlite3.connect(self.path)) as db: self.assertEqual(db.execute('SELECT count(*) FROM memory').fetchone()[0],0)
    def test_contradiction(self):
        r=self.m.append('a','s'); t=self.m.append('not a','s',contradicts=[r['id']]); self.assertEqual(t['status'],'unverified'); self.assertEqual(self.m.get(r['id']),r)
    def test_short_key(self):
        with self.assertRaises(ValueError): Memory(self.path,b'x')
    def test_invalid(self):
        with self.assertRaises(ValueError): self.m.append('','s')
if __name__=='__main__': unittest.main()
