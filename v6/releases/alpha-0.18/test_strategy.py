import unittest, tempfile, json, random
from core import Core, DemoProvider
from bridge import Application
from collective import Collective
from strategy import Strategy
from test_collective import Fixed
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.core=Core(self.tmp.name+'/db'); self.app=Application(self.core,None); self.s=Strategy(self.app)
    def tearDown(self): self.core.close(); self.tmp.cleanup()
    def test_exact_bypass(self):
        r=self.s.run('1/3+1/6'); self.assertEqual(r['conclusion'],'1/2'); self.assertEqual(r['provider_attempts'],0); self.assertFalse(r['authenticated'])
    def test_fallback(self):
        r=self.s.run('unknown',{'a':Fixed('yes'),'b':Fixed('yes')}); self.assertIsNone(r['conclusion']); self.assertEqual(r['provider_attempts'],2)
    def test_recovery(self):
        c=self.s.collective
        with self.assertRaises(KeyboardInterrupt): self.interrupt(c)
        ids=c.recover_interrupted(); self.assertEqual(len(ids),1); self.assertEqual(c.get(ids[0])['status'],'interrupted'); self.assertEqual(len(c.get(ids[0])['attempts']),1); self.assertEqual(c.recover_interrupted(),[])
    def interrupt(self,c):
        class Stop:
            def reason(self,q): raise KeyboardInterrupt()
        c.run('q',{'a':Fixed('x'),'b':Stop()})
    def test_budget(self):
        c=self.s.collective; self.assertRaises(ValueError,c.run,'q',{'a':Fixed('x'),'b':Fixed('y')},budget=1)
        r=c.run('q',{'a':DemoProvider(),'b':DemoProvider()},budget=1e-12); self.assertEqual(r['status'],'partial'); self.assertTrue(all(x['error']=='TimeoutError' for x in r['attempts']))
    def test_seeded(self):
        rng=random.Random(20261126)
        for _ in range(100):
            a,b=rng.randrange(-100,100),rng.randrange(-100,100); r=self.s.run(f'{a}+({b})'); self.assertEqual(r['conclusion'],str(a+b)); self.assertEqual(r['provider_attempts'],0)
