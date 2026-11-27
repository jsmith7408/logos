"""Strict structured claim comparison; no natural-language entailment or truth inference."""
import json, uuid
from itertools import combinations

FIELDS={'subject','predicate','object','scope','polarity'}
def parse(raw):
    if not isinstance(raw,str) or len(raw)>65536: raise ValueError('invalid claim payload')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result: raise ValueError('duplicate key')
            result[k]=v
        return result
    try: claims=json.loads(raw,object_pairs_hook=unique)
    except (ValueError,RecursionError) as exc: raise ValueError('invalid claim JSON') from exc
    if not isinstance(claims,list) or not 1<=len(claims)<=10: raise ValueError('invalid claim count')
    for c in claims:
        if not isinstance(c,dict) or set(c)!=FIELDS or type(c['polarity']) is not bool: raise ValueError('invalid claim schema')
        if any(not isinstance(c[k],str) or not c[k].strip() or len(c[k])>500 for k in FIELDS-{'polarity'}): raise ValueError('invalid claim field')
    return claims

def relation(a,b):
    if any(a[k]!=b[k] for k in FIELDS-{'polarity'}): return 'undetermined'
    return 'structured_agreement' if a['polarity']==b['polarity'] else 'structured_opposition'

class Claims:
    def __init__(self,collective):
        self.collective=collective; self.db=collective.db
        with self.db: self.db.execute('CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def run(self,source):
        original=self.collective.get(source)
        if original['status'] not in ('complete','partial'): raise ValueError('unfinished investigation')
        report=dict(id=str(uuid.uuid4()),source=source,classification='unverified',authenticated=False,conclusion=None,claims=[],rejected=[],relations=[])
        for attempt in original['attempts']:
            rid=attempt.get('record')
            if not rid: continue
            row=self.db.execute('SELECT result,provenance FROM research WHERE id=?',(rid,)).fetchone()
            try:
                if not row or row[1]!='unverified_provider': raise ValueError('not a provider claim')
                parsed=parse(row[0])
            except ValueError:
                report['rejected'].append(rid); continue
            for c in parsed: report['claims'].append(dict(record=rid,provider=attempt['provider'],claim=c))
        for (i,a),(j,b) in combinations(enumerate(report['claims']),2):
            if a['record']!=b['record']: report['relations'].append(dict(left=i,right=j,relation=relation(a['claim'],b['claim'])))
        with self.db: self.db.execute('INSERT INTO claims VALUES (?,?)',(report['id'],json.dumps(report)))
        return report
