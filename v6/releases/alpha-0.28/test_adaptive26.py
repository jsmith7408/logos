import tempfile, unittest
from unittest.mock import patch
from core import Core
from bridge import Application
from strategy import Strategy
from providers import OllamaProvider

class Adaptive26Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'; self.open()
    def open(self):
        self.c=Core(self.path); self.s=Strategy(Application(self.c,None)); self.a=self.s.adaptive
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def test_introspection(self):
        r=self.a.reflect(); self.assertIn('experiment',r['structure']['functions']); self.assertFalse(r['authenticated']); self.assertEqual(len(r['structure']['source_sha256']),64)
    def test_improvement_activation_and_rollback(self):
        r=self.a.experiment('trim-v1',activate=True); self.assertTrue(r['activated']); self.assertEqual(r['regressions'],0); self.assertEqual(r['candidate_correct'],r['total']); self.assertEqual(self.s.run(' 2+3 ',native_only=True)['conclusion'],'5')
        self.c.close(); self.open(); self.assertEqual(self.a.active(),'trim-v1'); self.a.rollback(); self.assertEqual(self.a.active(),'exact-v1')
    def test_negative_control(self):
        r=self.a.experiment('negative-control',activate=True); self.assertFalse(r['activated']); self.assertGreater(r['regressions'],0); self.assertEqual(self.a.active(),'exact-v1')
    def test_no_automatic_activation(self):
        self.assertTrue(self.a.experiment('trim-v1')['eligible']); self.assertEqual(self.a.active(),'exact-v1')
    def test_reject_injection_and_no_gain(self):
        with self.assertRaises(ValueError): self.a.experiment('exec("bad")',activate=True)
        self.assertFalse(self.a.experiment('exact-v1',activate=True)['activated'])
    def test_quarantine(self):
        r=self.a.quarantine('A'); self.assertEqual(r['symbolic_status'],'unknown'); self.assertEqual(self.s.knowledge.infer('A')['status'],'unknown'); self.assertEqual(self.c.db.execute('SELECT count(*) FROM native_facts').fetchone()[0],0)
    def test_falsification(self):
        self.s.knowledge.fact('!A','local'); self.assertEqual(self.a.quarantine('A')['symbolic_status'],'refuted')
    def test_native_first(self):
        self.s.knowledge.fact('A','local'); p=OllamaProvider('test')
        with patch.object(p,'reason',side_effect=AssertionError('provider called')): self.assertEqual(self.a.investigate('A',local_model=p)['provider_attempts'],0)
        self.assertEqual(self.a.investigate('B')['provider_attempts'],0)
    def test_optional_model_quarantine(self):
        p=OllamaProvider('test')
        with patch.object(p,'reason',return_value='A'): r=self.a.investigate('A',local_model=p)
        self.assertEqual(r['proposal']['symbolic_status'],'unknown'); self.assertFalse(r['proposal']['promoted']); self.assertEqual(self.s.knowledge.infer('A')['status'],'unknown')
        with patch.object(p,'reason',return_value='B'): self.assertTrue(self.a.investigate('A',local_model=p)['proposal_rejected'])
    def test_calibration(self):
        self.assertIsNone(self.a.calibration()['brier']); self.a.score_prediction('2+2','4',.9); self.a.score_prediction('2+2','5',.8); r=self.a.calibration(); self.assertEqual(r['accuracy'],.5); self.assertAlmostEqual(r['brier'],.325)
        with self.assertRaises(ValueError): self.a.score_prediction('2+2','4',float('nan'))
    def test_history_bound(self):
        self.a.LIMIT=2
        for _ in range(3): self.a.quarantine('A')
        self.assertEqual(len(self.a.recent('hypothesis_quarantine')),2)
