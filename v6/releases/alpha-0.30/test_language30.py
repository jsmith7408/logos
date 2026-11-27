import unittest,tempfile,math,json
from core import Core
from bridge import Application
from strategy import Strategy
from language30 import AttentionModel,Language30,rows,vocabulary,pieces,encode_json,digest

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.open()
    def open(self):
        self.c=Core(self.tmp.name+'/db'); self.s=Strategy(Application(self.c,None)); self.l=Language30(self.s)
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def data(self):
        for split,text in [('train','logos learns logic. logos learns facts. research tests evidence. '*3),('validation','logos learns facts. research learns logic.'),('test','research tests logic. logos learns evidence.')]:
            self.l.add(text,'test '+split,split,approved=True)
    def train(self):
        self.data(); r=self.l.train(30,8,3); self.assertTrue(r['eligible']); return r
    def test_gradient(self):
        m=AttentionModel(['<unk>','<bos>','<eos>','a','b'],7); ctx=(1,3,1,3); y=4; epsilon=1e-5
        for field,i,j in [('e',3,0),('e',1,2),('h',0,0),('w',4,3),('pos',1,None),('b',4,None),('hb',0,None)]:
            vector=getattr(m,field); vector=vector[i] if j is not None else vector; k=j if j is not None else i; old=vector[k]
            vector[k]=old+epsilon; hi=m.loss([(ctx,y)]); vector[k]=old-epsilon; lo=m.loss([(ctx,y)]); vector[k]=old
            clone=AttentionModel.load(m.state()); clone.step(ctx,y,.001); changed=getattr(clone,field); actual=changed[i][j] if j is not None else changed[i]
            self.assertAlmostEqual((old-actual)/.001,(hi-lo)/(2*epsilon),places=6)
    def test_subwords_train_only(self):
        v=vocabulary(['cat cat car']); self.assertIn('w:cat',v); self.assertNotIn('w:cart',v); self.assertEqual(pieces('cart',{'cat'}),['c:▁','c:c','c:a','c:r','c:t']); self.assertEqual(sum(y==0 for _,y in rows(['cat z'],v)),1)
    def test_split_and_duplicate(self):
        with self.assertRaises(ValueError): self.l.add('a b c','test','train')
        self.l.add('a b c','test','train',approved=True)
        with self.assertRaises(ValueError): self.l.add('A B C','other','test',approved=True)
        with self.assertRaises(ValueError): self.l.train()
    def test_train_validation_gate_and_restart(self):
        r=self.train(); self.assertLess(r['final']['validation'],r['initial']['validation']); self.assertLessEqual(r['final']['test'],r['initial']['test']); self.assertIsNone(self.l.active_id())
        with self.assertRaises(ValueError): self.l.activate(r['checkpoint'])
        self.l.activate(r['checkpoint'],approved=True); g=self.l.generate('logos learns'); self.assertFalse(g['authenticated']); self.c.close(); self.open(); self.assertEqual(g,self.l.generate('logos learns')); self.assertIsNone(self.l.rollback(approved=True)); self.assertIsNone(self.l.active_id())
    def test_reject_bad_candidate(self):
        self.data(); split,v,d=self.l.dataset(); m=AttentionModel(v,17); m.b[0]=100.0
        payload=encode_json({'state':m.state(),'dataset':split,'baseline':None,'seed':17,'best_epoch':1}); key=digest(payload)
        with self.c.db: self.c.db.execute('INSERT INTO l30_models VALUES (?,?,?)',(key,payload,'{}'))
        with self.assertRaisesRegex(ValueError,'regression gate'): self.l.activate(key,approved=True)
        self.assertIsNone(self.l.active_id())
    def test_stale_and_tampered_checkpoint(self):
        r=self.train(); self.l.add('new facts arise.','new','train',approved=True)
        with self.assertRaises(ValueError): self.l.activate(r['checkpoint'],approved=True)
        with self.c.db: self.c.db.execute("UPDATE l30_models SET payload='{}'")
        with self.assertRaises(ValueError): self.l.load(r['checkpoint'])
    def test_grounded_and_web_quarantine(self):
        text='logos supports A.'; url='https://example.com/'; sha=digest(text); key=digest(url+'\n'+sha); rec={'id':key,'url':url,'text':text,'sha256':sha}
        with self.c.db: self.c.db.execute('INSERT INTO native28_web VALUES (?,?)',(key,json.dumps(rec)))
        with self.assertRaises(ValueError): self.l.review_web(key,text,'train')
        with self.assertRaises(ValueError): self.l.review_web(key,'fabricated','train',approved=True)
        self.l.review_web(key,text,'train',approved=True); self.assertEqual(self.s.knowledge.infer('A')['status'],'unknown'); self.assertEqual(self.l.converse('what is truth?')['status'],'abstain'); self.assertEqual(self.l.converse('calculate 2+2')['result']['strategy'],'exact_arithmetic')
    def test_bounds(self):
        self.data()
        for kwargs in [{'epochs':0},{'patience':0},{'seed':-1}]:
            with self.assertRaises(ValueError): self.l.train(**kwargs)
        with self.assertRaises(ValueError): self.l.generate('a',33)
        with self.assertRaises(ValueError): self.l.generate('a')
