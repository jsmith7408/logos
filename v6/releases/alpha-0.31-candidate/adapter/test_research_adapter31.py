import unittest,tempfile,sqlite3
from pathlib import Path
from research_adapter31 import record
class AdapterTests(unittest.TestCase):
    def test_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'research.db'; q='A is 5; B is 2 times A; find B'
            a=record(p,q); self.assertEqual(a['result']['answer'],'10'); self.assertEqual(a['evidence_status'],'unverified'); self.assertIsNone(a['confidence']); self.assertEqual(a,record(p,q))
            with sqlite3.connect(p) as c: self.assertEqual(c.execute('SELECT count(*) FROM experimental_reasoning').fetchone()[0],1)
    def test_abstain(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(record(Path(d)/'db','unknown')['result']['status'],'abstain')
    def test_limit(self):
        with self.assertRaises(ValueError): record(':memory:','x'*4097)
