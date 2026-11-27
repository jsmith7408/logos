import unittest,tempfile
from core import Core
from bridge import Application
from strategy import Strategy
from providers import OllamaProvider
from unittest.mock import patch
class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.c=Core(self.tmp.name+'/db'); self.s=Strategy(Application(self.c,None)); self.a=self.s.acquisition
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def test_native(self):
        with patch.object(OllamaProvider,'reason',side_effect=AssertionError):
            r=self.a.extract('Oak is a Tree','book',local_model=OllamaProvider('test'))
        self.assertEqual(r['subject'],'Oak'); self.assertFalse(r['authenticated']); self.assertEqual(r['provider_attempts'],0)
        self.assertEqual(self.s.knowledge.infer('Oak')['status'],'unknown')
    def test_abstain(self): self.assertEqual(self.a.extract('unknown prose','s')['status'],'abstained')
    def test_model_gate(self):
        with patch.object(OllamaProvider,'reason',return_value='Oak is a Tree'):
            self.assertEqual(self.a.extract('No such claim','s',local_model=OllamaProvider('test'))['status'],'abstained')
            self.assertEqual(self.a.extract('Text: Oak is a Tree','s',local_model=OllamaProvider('test'))['status'],'candidate')
    def test_priority(self):
        a=self.s.planner.create('A'); b=self.s.planner.create('B'); self.s.planner.run(b); self.assertEqual(self.a.prioritize()[0]['objective'],b)
    def test_dedup(self):
        self.a.extract('A causes B','s'); self.a.extract('A causes B','s'); self.assertEqual(self.c.db.execute('SELECT count(*) FROM semantic_candidates').fetchone()[0],1)
