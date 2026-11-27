import json, sys
from enforcement import BoundUnified
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def dispatch(engine, request):
    if type(request) is not dict: raise ValueError('request object required')
    action=request.get('action')
    if action=='identity' and set(request)=={'action'}: return {'deployment':engine.deployment}
    if action=='administer' and set(request)=={'action','operation','signature'}:
        engine.administer(request['operation'],bytes.fromhex(request['signature'])); return {'status':'accepted'}
    if action=='compare' and set(request)=={'action','study','key','questions','baseline','settings','b','c','bm','cm','bs','cs'}:
        return engine.compare(request['study'],request['key'],*(bytes.fromhex(request[k]) for k in ('questions','baseline','settings','b','c')),request['bm'],request['cm'],bytes.fromhex(request['bs']),bytes.fromhex(request['cs']))
    raise ValueError('unsupported request')

def main():
    engine=BoundUnified(sys.argv[1],Ed25519PublicKey.from_public_bytes(bytes.fromhex(sys.argv[2])))
    try:
        for line in sys.stdin:
            try: result=dispatch(engine,json.loads(line))
            except Exception: result={'status':'blocked'}
            print(json.dumps(result,allow_nan=False),flush=True)
    finally: engine.close()
if __name__=='__main__': main()
