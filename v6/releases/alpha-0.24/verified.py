"""Local HMAC attestations: authenticate configured key holders, not truth."""
import hashlib,hmac,json
class Verified:
    def __init__(self,strategy):
        self.strategy=strategy; self.db=strategy.db; self.trust={}
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS attestations(id TEXT PRIMARY KEY, record TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS promoted(literal TEXT PRIMARY KEY, evidence TEXT NOT NULL)')
    def configure(self,source,key,origin):
        if not isinstance(key,bytes) or len(key)<32 or not source or not origin: raise ValueError('invalid trust configuration')
        self.trust[source]=(key,origin)
    @staticmethod
    def payload(source,excerpt):
        return json.dumps([source,excerpt],separators=(',',':')).encode()
    def acquire(self,source,excerpt,signature):
        if source not in self.trust or not isinstance(excerpt,str) or len(excerpt)>2000: raise ValueError('untrusted evidence')
        key,origin=self.trust[source]
        if not hmac.compare_digest(hmac.new(key,self.payload(source,excerpt),hashlib.sha256).hexdigest(),signature): raise ValueError('invalid signature')
        r=self.strategy.acquisition.extract(excerpt,source)
        if r['status']!='candidate': return r
        r.update(origin=origin,signature=signature,authenticated=True)
        with self.db: self.db.execute('INSERT OR IGNORE INTO attestations VALUES (?,?)',(r['id'],json.dumps(r)))
        return r
    @staticmethod
    def literal(r):
        p='is a' if r['predicate']=='is not a' else r['predicate']
        return ('!' if r['predicate']=='is not a' else '')+'rel_'+hashlib.sha256(json.dumps([r['subject'],p,r['object']]).encode()).hexdigest()[:60]
    def assess(self,literal):
        from knowledge import atom,opposite
        atom(literal); support=[]; opposition=[]; origins=set(); keys=set()
        rows=self.db.execute('SELECT record FROM attestations ORDER BY id LIMIT 10001').fetchall()
        if len(rows)>10000: raise ValueError('evidence budget exceeded')
        for (raw,) in rows:
            r=json.loads(raw); config=self.trust.get(r['source'])
            if not config: continue
            key,origin=config
            if not hmac.compare_digest(hmac.new(key,self.payload(r['source'],r['excerpt']),hashlib.sha256).hexdigest(),r['signature']): continue
            # Reparse signed content, never trust stored semantic fields.
            from acquisition import PATTERN
            m=PATTERN.fullmatch(r['excerpt'].strip())
            if not m or tuple(r[k] for k in ('subject','predicate','object'))!=m.groups(): continue
            l=self.literal(r)
            if l==opposite(literal): opposition.append(r['id'])
            if l==literal and origin not in origins and key not in keys:
                origins.add(origin); keys.add(key); support.append(r['id'])
        return dict(support=support,opposition=opposition,eligible=len(support)>=2 and not opposition)
    def promote(self,literal):
        report=self.assess(literal)
        if not report['eligible']: return report
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO promoted VALUES (?,?)',(literal,json.dumps(report)))
            self.db.execute('INSERT OR IGNORE INTO native_facts VALUES (?,?)',(literal,'attested:'+literal))
        return report
    def continue_research(self,limit=8):
        return [self.strategy.planner.resume(r['objective']) for r in self.strategy.acquisition.prioritize(limit)]
