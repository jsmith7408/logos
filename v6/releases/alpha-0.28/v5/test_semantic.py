import unittest,json
from test_lifecycle import Lifecycle
from secure import canonical,digest
class Semantic(Lifecycle):
 def resign(self):
    s=self.s;s.bs=s.p.sign(canonical(s.bm));s.cs=s.p.sign(canonical(s.cm))
 def test_changed_metadata(self):
    self.pair();self.s.bm['nonce']='new';self.resign();self.assertEqual(self.pair()['status'],'blocked')
 def test_reformat(self):
    self.pair();s=self.s;s.b=json.dumps(json.loads(s.b),indent=2).encode();s.bm['sha256']=digest(s.b);self.resign();self.assertEqual(self.pair()['status'],'blocked')
 def test_different_model(self):
    self.pair();self.s.bm['model']=self.s.cm['model']='different';self.resign();self.assertEqual(self.pair()['status'],'candidate_comparison')
 def test_legacy(self):
    self.g.db.execute('INSERT INTO consumed VALUES(?,?)',('old','old'));self.assertEqual(self.pair()['reason'],'legacy ledger requires migration')
 def test_changed_signer(self):
    self.pair();self.g.enroll('alias',self.pub);self.s.bm['signer']=self.s.cm['signer']='alias';self.resign();self.assertEqual(self.pair()['status'],'blocked')
