"""Bounded deterministic Boolean structural causal models in topological order."""
def causal(model, intervention, query):
    if type(model) is not list or not 1 <= len(model) <= 32 or type(intervention) is not dict:
        raise ValueError('model budget')
    names=set(); rows=[]
    for row in model:
        if type(row) is not dict or set(row)!={'name','parents','table'}: raise ValueError('row')
        n,p,t=row['name'],row['parents'],row['table']
        if type(n) is not str or not n.isidentifier() or len(n)>64 or n in names: raise ValueError('name')
        if type(p) is not list or len(p)>8 or any(type(x) is not str or x not in names for x in p) or len(set(p))!=len(p): raise ValueError('parents')
        if type(t) is not list or len(t)!=2**len(p) or any(type(x) is not bool for x in t): raise ValueError('table')
        names.add(n); rows.append((n,p,t))
    if type(query) is not str or query not in names or any(k not in names or type(v) is not bool for k,v in intervention.items()): raise ValueError('query or intervention')
    def evaluate(overrides):
        result={}
        for n,p,t in rows:
            idx=0
            for x in p: idx=2*idx+result[x]
            result[n]=overrides[n] if n in overrides else t[idx]
        return result
    factual=evaluate({}); changed=evaluate(intervention)
    return {'status':'solved','factual':factual[query],'counterfactual':changed[query],'changed':factual[query]!=changed[query],'confidence':None}
