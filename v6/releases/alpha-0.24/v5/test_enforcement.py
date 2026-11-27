import unittest,tempfile
from enforcement import BoundUnified
from unified import Unified
from secure import canonical
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
class Tests(unittest.TestCase):
 def test_binding(self):
    with tempfile.TemporaryDirectory() as t:
        a=Ed25519PrivateKey.generate(); b=Ed25519PrivateKey.generate(); p=t+'/a'; u=BoundUnified(p,a.public_key()); v=BoundUnified(t+'/b',a.public_key())
        op=dict(deployment=u.deployment,action='study',nonce='1',id='s',binding={}); sig=a.sign(canonical(op)); u.administer(op,sig)
        with self.assertRaises(ValueError): v.administer(op,sig)
        with self.assertRaises(Exception): v.administer(dict(op,deployment=v.deployment),sig)
        ident=u.deployment; u.close(); v.close()
        with self.assertRaises(ValueError): BoundUnified(p,b.public_key())
        u=BoundUnified(p,a.public_key()); self.assertEqual(u.deployment,ident); u.close()
 def test_legacy(self):
    with tempfile.TemporaryDirectory() as t:
        a=Ed25519PrivateKey.generate(); p=t+'/a'; u=Unified(p,a.public_key()); op=dict(action='study',nonce='1',id='s',binding={}); u.administer(op,a.sign(canonical(op))); u.close()
        with self.assertRaises(ValueError): BoundUnified(p,a.public_key())
