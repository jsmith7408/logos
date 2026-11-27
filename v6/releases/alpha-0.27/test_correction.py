import unittest, random
from fractions import Fraction
from core import Core, DemoProvider
from bridge import Application
from collective import Collective
from correction import Correction
from test_collective import Fixed

class Tests(unittest.TestCase):
    def setUp(self):
        self.core=Core(':memory:'); self.c=Collective(Application(self.core,None)); self.r=Correction(self.c)
    def tearDown(self): self.core.close()
    def test_preserve_and_correct(self):
        source=self.c.run('1/2',{'a':Fixed('2/4'),'b':Fixed('3')})
        r=self.r.run(source['id']); self.assertEqual([d['action'] for d in r['decisions']],['preserve','correct']); self.assertEqual([d['revised'] for d in r['decisions']],['2/4','1/2']); self.assertEqual(self.r.get(r['id']),r); self.assertEqual(self.c.get(source['id']),source); self.assertFalse(r['authenticated'])
    def test_abstain(self):
        r=self.r.run(self.c.run('1+1',{'a':DemoProvider(),'b':Fixed('unknown')})['id']); self.assertEqual([d['action'] for d in r['decisions']],['abstain']*2)
    def test_unsupported(self):
        with self.assertRaises(ValueError): self.r.run(self.c.run('2**3',{'a':Fixed('8'),'b':Fixed('9')})['id'])
        self.assertEqual(self.core.db.execute('SELECT count(*) FROM corrections').fetchone()[0],0)
    def test_seeded(self):
        rng=random.Random(20261126)
        for _ in range(100):
            a,b=rng.randint(-100,100),rng.randint(1,100); expected=Fraction(a,b)
            r=self.r.run(self.c.run(f'{a}/{b}',{'a':Fixed(str(expected)),'b':Fixed(str(expected+1))})['id'])
            self.assertEqual([d['action'] for d in r['decisions']],['preserve','correct']); self.assertTrue(all(Fraction(d['revised'])==expected for d in r['decisions']))
