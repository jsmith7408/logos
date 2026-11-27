import unittest,tempfile
from unittest.mock import patch
from core import Core
from bridge import Application
from strategy import Strategy
from native_research import evaluate
from web_evidence import fetch_public
P={'domain':'probability','prior':'1/3','likelihood':'3/4','alternative':'1/4'}
G={'domain':'graph','edges':[['A','B'],['B','C']],'start':'A','target':'C'}
class Native28Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.open()
    def open(self):
        self.c=Core(self.tmp.name+'/db'); self.s=Strategy(Application(self.c,None)); self.n=self.s.native
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def test_bayes(self):
        self.assertEqual(evaluate(P),'3/5')
        self.assertIsNone(evaluate(dict(P,likelihood='0',alternative='0')))
        with self.assertRaises(ValueError): evaluate(dict(P,prior='2'))
    def test_composition_quarantined(self):
        r=self.n.transfer({'domain':'composition','graph':G,'probability':P})
        self.assertEqual(r['result'],{'path':'reachable','posterior':'3/5','causal_effect':'not_identified'})
        self.assertFalse(r['promoted']); self.assertEqual(self.s.knowledge.infer('C')['status'],'unknown')
    def test_native_default(self):
        with patch.object(self.s.collective,'run',side_effect=AssertionError):
            self.assertEqual(self.s.run('unsupported question')['provider_attempts'],0)
    def test_lifecycle_and_restart(self):
        self.s.planner.create('C'); self.s.knowledge.rule(['A'],'C')
        self.assertIn('A',self.n.questions()); self.assertEqual(self.n.hypothesize('C')['status'],'unknown')
        self.s.knowledge.fact('A','manual'); self.assertEqual(self.n.hypothesize('C')['status'],'supported')
        self.c.close(); self.open(); self.assertEqual(self.n.status()['hypotheses'],1)
        self.s.multidomain.retract_manual('A','manual'); self.assertEqual(self.n.hypothesize('C')['status'],'unknown')
    def test_benchmark(self):
        r=self.n.import_benchmark([{'task':P,'expected':'3/5'}],'outside fixture')
        self.assertEqual(r['correct'],1); self.assertFalse(r['independence_verified']); self.assertFalse(r['activation'])
        with self.assertRaises(ValueError): self.n.import_benchmark([{'task':P,'expected':'0'}]*2,'x')
    def test_cycle(self):
        self.s.planner.create('A'); r=self.n.cycle(12,2); s=self.n.cycle(12,2)
        self.assertEqual(r['benchmark']['dataset_digest'],s['benchmark']['dataset_digest']); self.assertEqual(r['benchmark']['correct'],r['benchmark']['total']); self.assertLessEqual(r['allocated_trials'],32); self.assertEqual(r['provider_attempts'],0)
    def test_train_predict(self):
        self.n.train_language('logos learns facts. logos learns logic.')
        r=self.n.predict('logos'); self.assertEqual(r['text'],'logos learns facts .'); self.assertFalse(r['authenticated']); self.assertEqual(r['provider_attempts'],0)
        self.c.close(); self.open(); self.assertEqual(self.n.predict('logos'),r)
    def test_web_rejects(self):
        for u in ['http://example.com','https://example.com?x=1','https://user@example.com','https://evil.example','https://example.com:444/']:
            with patch('socket.getaddrinfo',side_effect=AssertionError):
                with self.assertRaises(ValueError): fetch_public(u,['example.com'])
        with patch('socket.getaddrinfo',return_value=[(0,0,0,'',('127.0.0.1',443))]),patch('web_evidence.PinnedHTTPS',side_effect=AssertionError):
            with self.assertRaises(ValueError): fetch_public('https://example.com',['example.com'])
    def test_web_quarantine(self):
        with patch('socket.getaddrinfo',return_value=[(0,0,0,'',('93.184.216.34',443))]),patch('web_evidence.PinnedHTTPS') as factory:
            conn=factory.return_value; response=conn.getresponse.return_value; response.status=200
            response.getheader.side_effect=lambda name,default: {'Content-Type':'text/plain'}.get(name,default)
            response.read1.side_effect=[b'A causes B.',b'']; r=self.n.fetch('https://example.com',['example.com'])
            self.assertFalse(r['authenticated']); self.assertEqual(r['bytes'],11); factory.assert_called_once_with('example.com','93.184.216.34'); conn.request.assert_called_once(); self.assertEqual(self.s.knowledge.infer('B')['status'],'unknown')
            response.status=302
            with self.assertRaises(ValueError): self.n.fetch('https://example.com',['example.com'])
