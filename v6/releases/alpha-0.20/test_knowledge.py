import unittest,tempfile
from core import Core
from bridge import Application
from strategy import Strategy
from knowledge import Knowledge

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'; self.core=Core(self.path); self.k=Knowledge(self.core.db)
    def tearDown(self):
        self.core.close(); self.tmp.cleanup()
    def test_chain(self):
        self.k.fact('A','source'); self.k.rule(['A'],'B'); self.k.rule(['B'],'C'); r=self.k.infer('C'); self.assertEqual(r['status'],'supported'); self.assertEqual(r['proof']['C']['premises'],['B']); self.assertFalse(r['authenticated'])
    def test_unknown_cycle(self):
        self.k.rule(['A'],'B'); self.k.rule(['B'],'A'); self.assertEqual(self.k.infer('A')['status'],'unknown'); self.k.fact('A','s'); self.assertEqual(self.k.infer('B')['status'],'supported')
    def test_conflict(self):
        self.k.fact('A','s'); self.k.rule(['A'],'!A'); self.assertEqual(self.k.infer('A')['status'],'conflict')
    def test_persistence_duplicate(self):
        self.k.fact('A','s'); self.k.fact('A','s'); self.core.close(); self.core=Core(self.path); self.k=Knowledge(self.core.db); self.assertEqual(self.k.infer('A')['proof']['A']['sources'],['s'])
    def test_budget(self):
        self.k.fact('A','s'); self.k.rule(['A'],'B'); self.assertEqual(self.k.infer('B',1)['status'],'budget_exhausted')
    def test_native_route(self):
        s=Strategy(Application(self.core,None)); s.collective.run=lambda *a,**k: self.fail('provider invoked'); self.k.fact('A','s'); self.assertEqual(s.run('infer:A',native_only=True)['conclusion'],'supported'); self.assertEqual(s.run('infer:B')['provider_attempts'],0)
    def test_refutation_and_validation(self):
        self.k.fact('!A','s'); self.assertEqual(self.k.infer('A')['status'],'refuted'); self.assertRaises(ValueError,self.k.fact,'A B','s')
