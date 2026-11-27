import json
from gate import inspect,pair
from score import score,compare

def evaluate(key,b,c,bmeta,cmeta):
    if b is None or c is None: return {'status':'blocked','reason':'missing response arm'}
    if not pair(bmeta,cmeta): return {'status':'blocked','reason':'unmatched conditions'}
    states=[inspect(raw,key,meta)[0] for raw,meta in [(b,bmeta),(c,cmeta)]]
    if states!=['candidate','candidate']: return {'status':'blocked','reason':'insufficient provenance','classifications':states}
    bo,_=score(key,json.loads(b)); co,_=score(key,json.loads(c))
    return {'status':'candidate_comparison','metrics':compare(bo,co)}
