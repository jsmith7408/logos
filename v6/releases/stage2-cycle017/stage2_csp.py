"""Bounded finite integer domains with binary relations and optional minimization."""
import operator
OPS={'eq':operator.eq,'ne':operator.ne,'lt':operator.lt,'le':operator.le,'gt':operator.gt,'ge':operator.ge}
def solve(domains, constraints, minimize=None, budget=10000):
    if type(domains) is not dict or not 1<=len(domains)<=12 or type(budget) is not int or not 1<=budget<=100000: raise ValueError('budget')
    for k,d in domains.items():
        if type(k) is not str or not k.isidentifier() or len(k)>64 or type(d) is not list or not 1<=len(d)<=16 or any(type(x) is not int or abs(x)>1000000 for x in d) or len(set(d))!=len(d): raise ValueError('domain')
    if type(constraints) is not list or len(constraints)>64: raise ValueError('constraints')
    for c in constraints:
        if type(c) is not list or len(c)!=3 or any(type(x) is not str for x in c) or c[0] not in domains or c[2] not in domains or c[1] not in OPS: raise ValueError('relation')
    if minimize is not None and (type(minimize) is not str or minimize not in domains): raise ValueError('objective')
    names=sorted(domains,key=lambda k:(len(domains[k]),k)); a={}; best=None; count=0; steps=0; exhausted=False
    def visit(i):
        nonlocal best,count,steps,exhausted
        if i==len(names):
            count+=1
            if best is None or (minimize is not None and a[minimize]<best[minimize]): best=dict(a)
            return
        k=names[i]
        for x in sorted(domains[k]):
            if steps>=budget: exhausted=True; return
            steps+=1; a[k]=x
            if all(l not in a or r not in a or OPS[o](a[l],a[r]) for l,o,r in constraints): visit(i+1)
            del a[k]
            if exhausted: return
    visit(0)
    return {'status':'budget_exhausted' if exhausted else 'unsatisfiable' if best is None else 'optimal' if minimize is not None else 'satisfiable','solution':best,'solutions_found':count,'steps':steps,'confidence':None}
