"""Bounded positive ground Horn rules; absence is not falsity."""
import re

def infer(facts, rules, query):
    def atom(x):
        if type(x) is not str or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', x):
            raise ValueError('atom')
        return x
    if type(facts) is not list or len(facts)>128 or type(rules) is not list or len(rules)>128:
        raise ValueError('budget')
    query=atom(query)
    proof={atom(f): {'fact':True} for f in facts}
    parsed=[]
    for r in rules:
        if type(r) is not dict or set(r)!={'if','then'} or type(r['if']) is not list or not 1<=len(r['if'])<=16:
            raise ValueError('rule')
        parsed.append(([atom(x) for x in r['if']],atom(r['then'])))
    for _ in range(len(parsed)+1):
        changed=False
        for i,(body,head) in enumerate(parsed):
            if head not in proof and all(x in proof for x in body):
                proof[head]={'rule':i,'premises':body}; changed=True
        if not changed: break
    return {'status':'entailed' if query in proof else 'unknown','proof':proof,'confidence':None}
