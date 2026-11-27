import unittest,tempfile
from core import Core
from bridge import Application
from strategy import Strategy
class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'; self.core=Core(self.path); self.s=Strategy(Application(self.core,None)); self.p=self.s.planner
        self.s.collective.run=lambda *a,**k:self.fail('provider called')
    def tearDown(self): self.core.close(); self.tmp.cleanup()
    def test_resume_after_restart(self):
        oid=self.p.create('A'); old=self.p.run(oid); self.core.close(); self.core=Core(self.path); self.s=Strategy(Application(self.core,None)); self.p=self.s.planner
        self.s.knowledge.fact('A','source'); new=self.p.resume(oid); self.assertEqual(new['previous_investigation'],old['id']); self.assertEqual(new['status'],'supported'); self.assertEqual(self.p.get(old['id']),old); self.assertFalse(new['authenticated'])
    def test_conflict_on_resume(self):
        oid=self.p.create('A'); self.s.knowledge.fact('A','s'); self.p.run(oid); self.s.knowledge.fact('!A','s'); self.assertEqual(self.p.resume(oid)['status'],'conflict')
    def test_history_order_limit(self):
        oid=self.p.create('A'); a=self.p.run(oid); b=self.p.resume(oid); self.assertEqual(self.p.history(oid),[b,a]); self.assertEqual(self.p.history(oid,limit=1),[b])
    def test_empty_and_invalid(self):
        oid=self.p.create('A'); self.assertEqual(self.p.history(oid),[]); self.assertNotIn('previous_investigation',self.p.resume(oid));
        with self.assertRaises(KeyError): self.p.resume('missing')
        with self.assertRaises(ValueError): self.p.history(oid,limit=True)
