"""Bounded propositional entailment by exhaustive truth assignments."""
import ast
from itertools import product

def entail(premises, conclusion):
    if type(premises) is not list or len(premises)>16:
        raise ValueError('premise budget')
    names=set()
    def parse(s):
        if type(s) is not str or not 0<len(s)<=256: raise ValueError('length')
        t=ast.parse(s,mode='eval').body
        nodes=list(ast.walk(t))
        if len(nodes)>64: raise ValueError('node budget')
        for n in nodes:
            if isinstance(n,ast.Name): names.add(n.id)
            elif isinstance(n,ast.Constant) and type(n.value) is bool: pass
            elif not isinstance(n,(ast.BoolOp,ast.And,ast.Or,ast.UnaryOp,ast.Not,ast.Load)): raise ValueError('syntax')
        return t
    ps=[parse(s) for s in premises]; c=parse(conclusion)
    if len(names)>10: raise ValueError('variable budget')
    def val(t,e):
        if isinstance(t,ast.Name): return e[t.id]
        if isinstance(t,ast.Constant): return t.value
        if isinstance(t,ast.UnaryOp): return not val(t.operand,e)
        return (all if isinstance(t.op,ast.And) else any)(val(v,e) for v in t.values)
    count=0; counter=None
    names=sorted(names)
    for bits in product((False,True),repeat=len(names)):
        e=dict(zip(names,bits))
        if all(val(p,e) for p in ps):
            count+=1
            if counter is None and not val(c,e): counter=e
    return {'status':'inconsistent' if not count else 'not_entailed' if counter is not None else 'entailed','counterexample':counter,'models':count,'confidence':None}
