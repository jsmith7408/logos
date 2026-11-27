import unittest,tempfile,json,math
from unittest.mock import patch
from core import Core
from bridge import Application
from strategy import Strategy
from language29 import Language29, Model, tokenize,digest
from web_evidence import fetch_public
class Language29Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.open()
    def open(self):
        self.c=Core(self.tmp.name+'/db'); self.s=Strategy(Application(self.c,None)); self.l=Language29(self.s)
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def trained(self):
        self.l.add('logos learns logic. logos learns facts. '*8,'test',approved=True); return self.l.train(17,12)
    def test_tokenizer(self):
        self.assertEqual(tokenize('Café, LOGOS!'),['café',',','logos','!'])
        with self.assertRaises(ValueError): tokenize('a '*5001)
    def test_gradient(self):
        m=Model(['<unk>','<bos>','<eos>','a'],1); h=1e-5; old=m.e[1][0]; m.e[1][0]=old+h; hi=m.loss([(1,1,3)]); m.e[1][0]=old-h; lo=m.loss([(1,1,3)]); m.e[1][0]=old; m.step(1,1,3,.001); self.assertAlmostEqual((old-m.e[1][0])/.001,(hi-lo)/(2*h),places=6)
    def test_training_and_checkpoint(self):
        r=self.trained(); self.assertLess(r['final_loss'],r['initial_loss']); self.assertFalse(r['activated']); self.assertEqual(r,self.l.train(17,12)); self.l.activate(r['checkpoint'],approved=True); g=self.l.generate('logos learns'); self.assertFalse(g['authenticated']); self.c.close(); self.open(); self.assertEqual(g,self.l.generate('logos learns')); self.assertTrue(self.l.similar('logos')['neighbors'])
    def test_approval(self):
        with self.assertRaises(ValueError): self.l.add('a b c','test')
        r=self.trained()
        with self.assertRaises(ValueError): self.l.activate(r['checkpoint'])
        with self.assertRaises(ValueError): self.l.generate('logos')
    def test_vocabulary_and_rollback(self):
        r=self.trained(); self.l.activate(r['checkpoint'],approved=True); self.l.add('new concept appears.','second',approved=True); q=self.l.train(17,12); self.assertGreater(q['vocab'],r['vocab']); self.l.activate(q['checkpoint'],approved=True); self.assertIn('concept',self.l.load().vocab); self.l.activate(r['checkpoint'],approved=True); self.assertNotIn('concept',self.l.load().vocab)
    def test_tamper(self):
        r=self.trained(); self.c.db.execute("UPDATE language29_checkpoints SET payload='{}'"); self.c.db.commit()
        with self.assertRaises(ValueError): self.l.activate(r['checkpoint'],approved=True)
    def test_web_review(self):
        text='Unverified web content about C.'; url='https://example.com/'; sha=digest(text); key=digest(url+'\n'+sha); rec={'id':key,'url':url,'text':text,'sha256':sha}
        self.c.db.execute('INSERT INTO native28_web VALUES (?,?)',(key,json.dumps(rec))); self.c.db.commit()
        with self.assertRaises(ValueError): self.l.approve_web(key,text)
        with self.assertRaises(ValueError): self.l.approve_web(key,'fabricated excerpt',approved=True)
        self.l.approve_web(key,text,approved=True); self.l.train(1,3); self.assertEqual(self.s.knowledge.infer('C')['status'],'unknown')
    def test_conversation(self):
        self.assertEqual(self.l.converse('what is truth?')['status'],'abstain'); self.s.knowledge.fact('A','test'); self.assertEqual(self.l.converse('Does LOGOS support A?')['inference']['status'],'supported'); r=self.l.converse('calculate 2+2'); self.assertEqual(r['result']['strategy'],'exact_arithmetic'); self.assertEqual(r['provider_attempts'],0)
    def test_policy(self):
        for u,h in [('https://api.openai.com/v1/models','api.openai.com'),('https://example.com/api','example.com'),('https://random.example/','random.example')]:
            with patch('socket.getaddrinfo',side_effect=AssertionError):
                with self.assertRaises(ValueError): fetch_public(u,[h])
