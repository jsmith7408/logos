import unittest,tempfile
from pathlib import Path
from bridge import Bridge,Application,GateUnavailable
from core import Core,DemoProvider
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
import sys
sys.path.insert(0,str(Path(__file__).parent/'v5'))
from secure import canonical,digest

class BridgeTests(unittest.TestCase):
 def setUp(self):
    self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup)
    self.a=Ed25519PrivateKey.generate(); self.s=Ed25519PrivateKey.generate()
    pub=lambda k:k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    self.g=Bridge(self.t.name+'/gate.db',pub(self.a)); self.core=Core(self.t.name+'/research.db'); self.addCleanup(self.core.close); self.app=Application(self.core,self.g)
    self.d=self.g.request({'action':'identity'})['deployment']; self.pub=pub(self.s)
    key={'x':'1'}; binding=dict(key_digest=digest(canonical(key)),questions_digest=digest(b'q'),baseline_digest=digest(b'a'),settings_digest=digest(b's'))
    self.admin(dict(action='enroll',nonce='1',id='trusted',pub=self.pub)); self.admin(dict(action='study',nonce='2',id='pilot',binding=binding))
    b=canonical([dict(id='x',answer=0,confidence=.9)]); c=canonical([dict(id='x',answer=1,confidence=.9)])
    m=dict(binding,model='fixture',version='1',study='pilot',signer='trusted',origin='raw'); bm=dict(m,arm='B',sha256=digest(b)); cm=dict(m,arm='C',sha256=digest(c))
    self.req=dict(action='compare',study='pilot',key=key,questions=b'q'.hex(),baseline=b'a'.hex(),settings=b's'.hex(),b=b.hex(),c=c.hex(),bm=bm,cm=cm,bs=self.s.sign(canonical(bm)).hex(),cs=self.s.sign(canonical(cm)).hex())
 def admin(self,op):
    op=dict(op,deployment=self.d); self.assertEqual(self.g.request(dict(action='administer',operation=op,signature=self.a.sign(canonical(op)).hex())),{'status':'accepted'})
 def test_valid_and_replay(self):
    self.assertEqual(self.app.compare(self.req)['status'],'candidate_comparison'); self.assertEqual(self.app.compare(self.req)['status'],'blocked')
 def test_invalid_then_valid(self):
    self.assertEqual(self.app.compare(dict(self.req,cs='00'))['status'],'blocked'); self.assertEqual(self.app.compare(self.req)['status'],'candidate_comparison')
 def test_revocation(self):
    self.admin(dict(action='revoke',nonce='3',id='trusted')); self.assertEqual(self.app.compare(self.req)['status'],'blocked')
 def test_wrong_authority(self):
    with self.assertRaises(GateUnavailable): Bridge(self.g.path,self.pub).request({'action':'identity'})
 def test_demo_separate(self):
    self.assertEqual(self.app.investigate('gravity',DemoProvider())['provenance'],'demo'); self.assertEqual(self.core.search('gravity')[0]['provenance'],'demo'); self.assertRaises(ValueError,self.app.compare,{'action':'identity'})
