import unittest,tempfile
from core import Core
from bridge import Application
from strategy import Strategy
class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'; self.core=Core(self.path); self.s=Strategy(Application(self.core,None)); self.p=self.s.planner
        self.s.collective.run=lambda *a,**k:self.fail('provider called')
    def tearDown(self): self.core.close(); self.tmp.cleanup()
    def runq(self,q,**kw): return self.p.run(self.p.create(q),**kw)
    def test_arithmetic(self): self.assertEqual(self.runq('1/3+1/6')['conclusion'],'1/2')
    def test_gap_hypothesis(self):
        self.s.knowledge.fact('A','source'); self.s.knowledge.rule(['A','B'],'C'); r=self.runq('C'); self.assertIn('B',r['gaps']); self.assertEqual(r['hypotheses'][0]['status'],'conditional_unverified'); self.assertEqual(self.s.knowledge.infer('C')['status'],'unknown')
    def test_no_evidence(self):
        self.s.knowledge.rule(['A'],'C'); self.assertEqual(self.runq('C')['hypotheses'],[])
    def test_conflict(self):
        self.s.knowledge.fact('A','s'); self.s.knowledge.fact('!A','s'); self.assertEqual(self.runq('A')['status'],'conflict')
    def test_persistence(self):
        r=self.runq('A'); self.core.close(); self.core=Core(self.path); self.p=Strategy(Application(self.core,None)).planner; self.assertEqual(self.p.get(r['id']),r); self.assertEqual(self.p.run(r['objective'])['status'],'unknown')
    def test_cycle_budget(self):
        self.s.knowledge.rule(['A'],'B'); self.s.knowledge.rule(['B'],'A'); r=self.runq('A',max_checks=1); self.assertTrue(r['truncated']); self.assertEqual(len(r['checks']),1); self.assertEqual(len(self.runq('A')['checks']),2)
    def test_abstention(self): self.assertEqual(self.runq('unstructured question')['status'],'unsupported')
    def test_invalid(self):
        with self.assertRaises(ValueError): self.runq('A',max_checks=0)
    def test_supported(self):
        self.s.knowledge.fact('A','s'); self.s.knowledge.rule(['A'],'B'); r=self.runq('B'); self.assertEqual(r['conclusion'],'supported'); self.assertFalse(r['authenticated']); self.assertEqual(r['provider_attempts'],0)
