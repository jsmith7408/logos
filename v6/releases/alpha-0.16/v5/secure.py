import json
from cryptography.exceptions import InvalidSignature
from gate import digest
from compare_gate import evaluate

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def verify(raw,meta,signature,registry,study,key):
    if not isinstance(meta,dict) or not key or not isinstance(study,str) or not study: return False
    try:
        pub=registry[meta['signer']]
        pub.verify(signature,canonical(meta))
        return (meta['study']==study and meta['key_digest']==digest(canonical(key)) and meta['sha256']==digest(raw) and meta['origin']=='raw')
    except (InvalidSignature,KeyError,TypeError,ValueError,AttributeError): return False

def compare_signed(key,b,c,bm,cm,bs,cs,registry,study):
    if not all(verify(raw,m,s,registry,study,key) for raw,m,s in ((b,bm,bs),(c,cm,cs))): return {'status':'blocked','reason':'signature or binding failure'}
    return evaluate(key,b,c,dict(bm,attestation_verified=True),dict(cm,attestation_verified=True))
