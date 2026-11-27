import unittest, tempfile, sqlite3
from pathlib import Path
from research_adapter31 import record
from audit31 import seal, retrieve

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'db'; self.key=b'k'*32
        self.id=record(self.db,'A is 5; find A')['id']
    def test_roundtrip(self):
        self.assertEqual(seal(self.db,self.id,self.key),retrieve(self.db,self.id,self.key))
        self.assertEqual(retrieve(self.db,self.id,self.key)['evidence_status'],'unverified')
    def test_wrong_key(self):
        seal(self.db,self.id,self.key)
        with self.assertRaises(ValueError): retrieve(self.db,self.id,b'x'*32)
    def test_tamper(self):
        seal(self.db,self.id,self.key)
        with sqlite3.connect(self.db) as c: c.execute("UPDATE experimental_reasoning SET payload='{}'")
        with self.assertRaises(ValueError): retrieve(self.db,self.id,self.key)
    def test_short_key(self):
        with self.assertRaises(ValueError): seal(self.db,self.id,b'x')
