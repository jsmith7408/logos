import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from secure import *
class Security(unittest.TestCase):
 def setUp(self):
    self.k={'x':'1'}; self.p=Ed25519PrivateKey.generate(); self.reg={'trusted':self.p.public_key()}; self.study='pilot'; self.b=canonical([dict(id='x',answer=0,confidence=.9)]); self.c=canonical([dict(id='x',answer=1,confidence=.9)]); m={k:'same' for k in ('model','version','settings_digest','questions_digest','baseline_digest')}; m.update(study=self.study,signer='trusted',origin='raw',key_digest=digest(canonical(self.k))); self.bm=dict(m,arm='B',sha256=digest(self.b)); self.cm=dict(m,arm='C',sha256=digest(self.c)); self.bs=self.p.sign(canonical(self.bm)); self.cs=self.p.sign(canonical(self.cm))
 def run_pair(self): return compare_signed(self.k,self.b,self.c,self.bm,self.cm,self.bs,self.cs,self.reg,self.study)
 def blocked(self): self.assertEqual(self.run_pair()['status'],'blocked')
 def test_valid(self): self.assertEqual(self.run_pair()['metrics']['gains'],1)
 def test_unsigned(self): self.cs=b''; self.blocked()
 def test_flag_forgery(self): self.cm['attestation_verified']=True; self.blocked()
 def test_wrong_key(self): self.reg['trusted']=Ed25519PrivateKey.generate().public_key(); self.blocked()
 def test_modified_data(self): self.c+=b' '; self.blocked()
 def test_rehashed_data(self): self.c+=b' '; self.cm['sha256']=digest(self.c); self.blocked()
 def test_study_replay(self): self.study='other'; self.blocked()
 def test_key_change(self): self.k={'x':'0'}; self.blocked()
 def test_empty_key(self): self.k={}; self.blocked()
 def test_same_arm(self): self.cm['arm']='B'; self.cs=self.p.sign(canonical(self.cm)); self.blocked()
 def test_signed_mismatch(self): self.cm['version']='other'; self.cs=self.p.sign(canonical(self.cm)); self.blocked()
 def test_legacy_bypass(self): self.assertEqual(evaluate(self.k,self.b,self.c,dict(self.bm,attestation_verified=True),dict(self.cm,attestation_verified=True))['status'],'candidate_comparison')
