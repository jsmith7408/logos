import unittest,tempfile,os,sqlite3
from test_secure import Security
from lifecycle import TrustGate
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
class Lifecycle(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory(); self.path=os.path.join(self.tmp.name,'trust.db'); self.g=TrustGate(self.path); self.s=Security(); self.s.setUp(); self.pub=self.s.p.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw); self.g.enroll('trusted',self.pub)
 def tearDown(self): self.g.close(); self.tmp.cleanup()
 def pair(self):
    s=self.s; return self.g.compare(s.k,s.b,s.c,s.bm,s.cm,s.bs,s.cs,s.study)
 def test_replay(self):
    self.assertEqual(self.pair()['status'],'candidate_comparison'); self.assertEqual(self.pair()['reason'],'replayed evidence')
 def test_restart(self):
    self.pair(); self.g.close(); self.g=TrustGate(self.path); self.assertEqual(self.pair()['reason'],'replayed evidence')
 def test_revoked(self):
    self.g.revoke('trusted'); self.assertEqual(self.pair()['status'],'blocked')
 def test_no_reenrollment(self):
    self.g.revoke('trusted'); self.assertRaises(sqlite3.IntegrityError,self.g.enroll,'trusted',self.pub)
 def test_invalid_not_consumed(self):
    sig=self.s.cs; self.s.cs=b''; self.assertEqual(self.pair()['status'],'blocked'); self.s.cs=sig; self.assertEqual(self.pair()['status'],'candidate_comparison')
