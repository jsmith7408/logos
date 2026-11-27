"""Restricted local extraction; candidates are never automatically promoted to facts."""
import re,json,hashlib
from providers import OllamaProvider

PATTERN=re.compile(r'([A-Za-z][A-Za-z0-9_]{0,63}) (is a|is part of|causes|is not a) ([A-Za-z][A-Za-z0-9_]{0,63})\.?')
class Acquisition:
    def __init__(self,strategy):
        self.strategy=strategy; self.db=strategy.db
        with self.db: self.db.execute('CREATE TABLE IF NOT EXISTS semantic_candidates(id TEXT PRIMARY KEY, record TEXT NOT NULL)')
    def extract(self,text,source,*,local_model=None):
        if not isinstance(text,str) or not 1<=len(text)<=2000 or not isinstance(source,str) or not 1<=len(source.strip())<=1000: raise ValueError('invalid evidence')
        m=PATTERN.fullmatch(text.strip()); route='native'; attempts=0
        if not m and local_model is not None:
            if type(local_model) is not OllamaProvider: raise ValueError('loopback Ollama only')
            attempts=1; route='local_model'
            raw=local_model.reason('Extract one exact sentence of form A is a B, A is part of B, A causes B, or A is not a B. Do not invent. Text: '+json.dumps(text))
            m=PATTERN.fullmatch(raw.strip())
            if m and m.group(0).rstrip('.') not in text: m=None
        if not m: return dict(status='abstained',route=route,provider_attempts=attempts)
        s,p,o=m.groups(); record=dict(subject=s,predicate=p,object=o,source=source,excerpt=m.group(0),authenticated=False,status='candidate',route=route,provider_attempts=attempts)
        key=hashlib.sha256(json.dumps([s,p,o,source,m.group(0)],ensure_ascii=False).encode()).hexdigest(); record['id']=key
        with self.db: self.db.execute('INSERT OR IGNORE INTO semantic_candidates VALUES (?,?)',(key,json.dumps(record)))
        return record
    def prioritize(self,limit=20):
        if type(limit) is not int or not 1<=limit<=100: raise ValueError('invalid limit')
        rows=self.db.execute('SELECT id FROM objectives ORDER BY rowid LIMIT 1000').fetchall(); ranked=[]
        for (oid,) in rows:
            h=self.strategy.planner.history(oid,limit=1); r=h[0] if h else None
            if r and r.get('status') in ('supported','refuted','local_arithmetic_check'): continue
            ranked.append(dict(objective=oid,priority=0 if not r else 1+len(r.get('gaps',[]))))
        return sorted(ranked,key=lambda r:-r['priority'])[:limit]
