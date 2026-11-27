import unittest, tempfile, sqlite3
from pathlib import Path
from orchestration31 import run
from audit31 import retrieve
from research_adapter31 import record

class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.db=Path(t.name)/'db'; self.key=b'k'*32; self.q='A is 5; find A'
    def test_roundtrip(self):
        a=run(self.db,self.q,self.key)
        self.assertEqual(a,retrieve(self.db,a['id'],self.key))
        self.assertEqual(a,run(self.db,self.q,self.key))
    def test_wrong_key(self):
        run(self.db,self.q,self.key)
        with self.assertRaises(ValueError): run(self.db,self.q,b'x'*32)
    def test_unsealed(self):
        record(self.db,self.q)
        with self.assertRaises(ValueError): run(self.db,self.q,self.key)
    def test_atomic(self):
        run(self.db,self.q,self.key)
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TRIGGER fail_seal BEFORE INSERT ON experimental_seals BEGIN SELECT RAISE(ABORT,'failure'); END")
        with self.assertRaises(sqlite3.IntegrityError): run(self.db,'B is 6; find B',self.key)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM experimental_reasoning').fetchone()[0],1)
    def test_limits(self):
        with self.assertRaises(ValueError): run(self.db,self.q,b'x')
        with self.assertRaises(ValueError): run(self.db,'x'*4097,self.key)
