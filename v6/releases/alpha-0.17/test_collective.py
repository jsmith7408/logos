import unittest,tempfile
from pathlib import Path
from core import Core, DemoProvider
from bridge import Application
from collective import Collective
class Fixed:
    def __init__(self,value): self.value=value
    def reason(self,q):
        if isinstance(self.value,Exception): raise self.value
        return self.value
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'db'; self.core=Core(self.path); self.c=Collective(Application(self.core,None))
    def tearDown(self): self.core.close(); self.tmp.cleanup()
    def test_agreement_not_truth(self):
        r=self.c.run('2+2',{'a':Fixed('5'),'b':Fixed('5')}); self.assertEqual(r['comparison'],'exact_agreement'); self.assertIsNone(r['conclusion']); self.assertEqual(r['classification'],'unverified')
    def test_difference_preserves_both(self):
        r=self.c.run('q',{'a':Fixed('4'),'b':Fixed('5')}); self.assertEqual(r['comparison'],'text_difference'); self.assertEqual({x['result'] for x in self.core.search('q')},{'4','5'})
    def test_failure_persistent(self):
        r=self.c.run('q',{'a':Fixed(RuntimeError()),'b':DemoProvider()}); self.assertEqual(r['status'],'partial'); self.assertEqual(r['comparison'],'insufficient'); self.assertEqual(r['attempts'][1]['provenance'],'demo'); self.core.close(); self.core=Core(self.path); self.assertEqual(Collective(Application(self.core,None)).get(r['id']),r)
    def test_budget_and_duplicate(self):
        p=Fixed('x'); self.assertRaises(ValueError,self.c.run,'q',{'a':p,'b':p}); self.assertRaises(ValueError,self.c.run,'q',{str(i):Fixed('x') for i in range(6)})
    def test_oversize(self):
        r=self.c.run('q',{'a':Fixed('x'*65537),'b':Fixed('ok')}); self.assertEqual(r['status'],'partial'); self.assertEqual(len(self.core.search('q')),1)
