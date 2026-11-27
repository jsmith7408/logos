import json, math, sys
from fractions import Fraction
from pathlib import Path

def score(key, rows):
    by={}
    for r in rows:
        i=r['id']
        if i not in key or i in by: raise ValueError('unknown or duplicate ID')
        by[i]=r
    ok={}; losses=[]
    for i,v in key.items():
        r=by.get(i,{})
        try:
            a=r['answer']; ok[i]=type(a) in (int,str) and Fraction(a)==Fraction(v)
        except (KeyError,ValueError,ZeroDivisionError,TypeError): ok[i]=False
        p=r.get('confidence')
        if type(p) in (int,float) and 0<=p<=1: losses.append((p-int(ok[i]))**2)
    return ok,dict(n=len(key),correct=sum(ok.values()),coverage=len(by),brier=sum(losses)/len(losses) if losses else None,confidence_coverage=len(losses))
def compare(a,b):
    gains=sum(not a[i] and b[i] for i in a); harms=sum(a[i] and not b[i] for i in a); n=gains+harms
    p=min(1,2*sum(math.comb(n,k) for k in range(min(gains,harms)+1))/2**n)
    return dict(gains=gains,harms=harms,accuracy_delta=(gains-harms)/len(a),mcnemar_p=p)
if __name__=='__main__':
    root=Path(__file__).parent; key=json.loads((root/'key.json').read_text()); arms={}; results={}
    for name,path in zip(('baseline','review','logos'),sys.argv[1:],strict=True):
        arms[name],results[name]=score(key,json.loads(Path(path).read_text()))
    results['logos_vs_review']=compare(arms['review'],arms['logos']); results['logos_vs_baseline']=compare(arms['baseline'],arms['logos']); results['review_vs_baseline']=compare(arms['baseline'],arms['review']); print(json.dumps(results,indent=2))
