import unittest,json
from gate import digest
from compare_gate import evaluate
class Tests(unittest.TestCase):
 def setUp(self):
    self.key={'x':'1'}; self.b=json.dumps([dict(id='x',answer=0,confidence=.9)]).encode(); self.c=json.dumps([dict(id='x',answer=1,confidence=.9)]).encode(); m={k:'same' for k in ('model','version','settings_digest','questions_digest','baseline_digest')}; self.bm=dict(m,arm='B',origin='raw',attestation_verified=True,sha256=digest(self.b)); self.cm=dict(m,arm='C',origin='raw',attestation_verified=True,sha256=digest(self.c))
 def run_pair(self): return evaluate(self.key,self.b,self.c,self.bm,self.cm)
 def test_missing(self): self.b=None; self.assertEqual(self.run_pair()['reason'],'missing response arm')
 def test_exploratory(self): self.cm['origin']='reconstructed'; self.assertEqual(self.run_pair()['reason'],'insufficient provenance')
 def test_mismatch(self): self.cm['version']='different'; self.assertEqual(self.run_pair()['reason'],'unmatched conditions')
 def test_valid(self): self.assertEqual(self.run_pair()['metrics']['gains'],1)
 def test_tamper(self): self.c+=b' '; self.assertEqual(self.run_pair()['reason'],'insufficient provenance')
