import unittest,tempfile
from core import Core,DemoProvider
from bridge import Application
from workflow import Workflow
class Tests(unittest.TestCase):
 def setUp(self):
    self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.path=self.t.name+'/db'; self.c=Core(self.path); self.addCleanup(self.c.close); self.w=Workflow(Application(self.c,None))
 def test_complete(self):
    r=self.w.run(['a','b'],DemoProvider(),2); self.assertEqual(r['status'],'complete'); self.assertEqual(len(r['steps']),2); self.assertEqual(self.c.search('a')[0]['provenance'],'demo')
 def test_budget(self):
    with self.assertRaises(ValueError): self.w.run(['a','b'],DemoProvider(),1)
    self.assertEqual(self.c.search(''),[])
 def test_failure_stops(self):
    class P:
      calls=0
      def reason(self,q):
        self.calls+=1
        if self.calls==2: raise RuntimeError('secret')
        return q
    p=P(); r=self.w.run(['a','b','c'],p); self.assertEqual(p.calls,2); self.assertEqual(r['status'],'failed'); self.assertEqual(r['steps'][1]['record'],'RuntimeError'); self.assertEqual(len(self.c.search('')),1)
 def test_reopen(self):
    r=self.w.run(['a'],DemoProvider()); c=Core(self.path)
    try: self.assertEqual(Workflow(Application(c,None)).status(r['id']),r)
    finally: c.close()
 def test_invalid_plan(self):
    for plan in ([],[' '],['x'*4001],'a'):
      with self.assertRaises(ValueError): self.w.run(plan,DemoProvider())
