import unittest,tempfile,sqlite3
from unified import Unified
from test_secure import Security
from secure import canonical,digest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from cryptography.exceptions import InvalidSignature
class UnifiedTests(unittest.TestCase):
 def setUp(self):
    self.t=tempfile.TemporaryDirectory(); self.path=self.t.name+'/db'; self.a=Ed25519PrivateKey.generate(); self.u=Unified(self.path,self.a.public_key()); self.s=Security(); self.s.setUp(); s=self.s
    self.binding=dict(key_digest=digest(canonical(s.k)),questions_digest=digest(b'q'),baseline_digest=digest(b'a'),settings_digest=digest(b's'))
    self.op=dict(action='enroll',nonce='1',id='trusted',pub=s.p.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()); self.admin(self.op)
    self.admin(dict(action='study',nonce='2',id=s.study,binding=self.binding))
    for m in (s.bm,s.cm): m.update(self.binding)
    s.bs=s.p.sign(canonical(s.bm));s.cs=s.p.sign(canonical(s.cm))
 def admin(self,op): self.u.administer(op,self.a.sign(canonical(op)))
 def pair(self,q=b'q'):
    s=self.s;return self.u.compare(s.study,s.k,q,b'a',b's',s.b,s.c,s.bm,s.cm,s.bs,s.cs)
 def tearDown(self): self.u.close();self.t.cleanup()
 def test_valid_restart(self):
    self.assertEqual(self.pair()['status'],'candidate_comparison');self.u.close();self.u=Unified(self.path,self.a.public_key());self.assertEqual(self.pair()['status'],'blocked')
 def test_admin_forgery(self):
    with self.assertRaises(InvalidSignature): self.u.administer(self.op,b'')
 def test_admin_replay(self):
    with self.assertRaises(sqlite3.IntegrityError): self.admin(self.op)
 def test_binding(self): self.assertEqual(self.pair(b'changed')['status'],'blocked');self.assertEqual(self.pair()['status'],'candidate_comparison')
 def test_signature(self): self.s.cs=b'';self.assertEqual(self.pair()['status'],'blocked')
 def test_revocation(self): self.admin(dict(action='revoke',nonce='3',id='trusted'));self.assertEqual(self.pair()['status'],'blocked')
