import hashlib,json
from fractions import Fraction

def digest(data): return hashlib.sha256(data).hexdigest()

def inspect(raw, expected, manifest):
    issues=[]
    if digest(raw)!=manifest.get('sha256'): issues.append('hash mismatch')
    try:
        rows=json.loads(raw)
        if not isinstance(rows,list): raise ValueError()
        ids=[]
        for r in rows:
            ids.append(r['id'])
            if type(r['answer']) not in (str,int): raise ValueError()
            Fraction(r['answer'])
            c=r['confidence']
            if type(c) not in (float,int) or not 0<=c<=1: raise ValueError()
        if len(ids)!=len(set(ids)) or set(ids)!=set(expected): issues.append('coverage or duplicate error')
    except (ValueError,TypeError,KeyError,ZeroDivisionError): issues.append('invalid response')
    if issues: return 'rejected',issues
    if manifest.get('origin')!='raw' or not manifest.get('attestation_verified'):
        return 'exploratory',['raw independently attested provenance unavailable']
    return 'candidate',[]

def pair(b,c):
    fields=('model','version','settings_digest','questions_digest','baseline_digest')
    return (b.get('arm')=='B' and c.get('arm')=='C' and all(isinstance(b.get(k),str) and b[k] and b[k]==c.get(k) for k in fields))
