import unittest, tempfile, subprocess, sys, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from secure import canonical
class ServiceTests(unittest.TestCase):
 def test_boundary(self):
    with tempfile.TemporaryDirectory() as t:
        a=Ed25519PrivateKey.generate(); args=[sys.executable,'service.py',t+'/db',a.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()]
        def run(rows):
            p=subprocess.run(args,input='\n'.join(rows)+'\n',text=True,capture_output=True,check=True); return [json.loads(x) for x in p.stdout.splitlines()]
        ident=run(['{"action":"identity"}'])[0]['deployment']
        op=dict(deployment=ident,action='study',nonce='1',id='s',binding={}); req=json.dumps(dict(action='administer',operation=op,signature=a.sign(canonical(op)).hex()))
        out=run(['{"action":"enroll"}','{"action":"_gate"}','{"action":"identity","extra":1}','not json',req,req,'{"action":"identity"}'])
        self.assertEqual(out[:4],[{'status':'blocked'}]*4); self.assertEqual(out[4],{'status':'accepted'}); self.assertEqual(out[5],{'status':'blocked'}); self.assertEqual(out[6]['deployment'],ident)
