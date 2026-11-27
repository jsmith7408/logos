import unittest
from test_collective import Fixed
from collective import Collective
from core import Core, DemoProvider
from bridge import Application
from adjudication import Adjudicator,evaluate
from fractions import Fraction
class Tests(unittest.TestCase):
    def setUp(self):
        self.core=Core(':memory:'); self.c=Collective(Application(self.core,None)); self.a=Adjudicator(self.c)
    def tearDown(self): self.core.close()
    def run_pair(self,q,a,b): return self.c.run(q,{'a':Fixed(a),'b':Fixed(b)})
    def test_false_consensus(self):
        r=self.run_pair('2+2','5','5'); x=self.a.run(r['id']); self.assertEqual(x['conclusion'],'4'); self.assertEqual([f['status'] for f in x['findings']],['incorrect']*2); self.assertEqual(self.c.get(r['id']),r); self.assertFalse(x['authenticated']); self.assertEqual(self.a.get(x['id']),x)
    def test_equivalent(self):
        x=self.a.run(self.run_pair('1/2','0.5','2/4')['id']); self.assertEqual([f['status'] for f in x['findings']],['correct']*2)
    def test_unsupported(self):
        for q in ['2**3','__import__("os")','1.2+3','True','1/0']:
            with self.assertRaises((ValueError,ZeroDivisionError)): evaluate(q)
    def test_unparseable(self):
        x=self.a.run(self.run_pair('1+1','2 because math','1/0')['id']); self.assertEqual([f['status'] for f in x['findings']],['unparseable']*2)
    def test_demo(self):
        r=self.c.run('1+1',{'a':DemoProvider(),'b':Fixed('2')}); self.assertEqual(self.a.run(r['id'])['findings'][0]['status'],'demonstration')
    def test_exact(self): self.assertEqual(evaluate('-(1/3)+2/7'),Fraction(-1,21))
