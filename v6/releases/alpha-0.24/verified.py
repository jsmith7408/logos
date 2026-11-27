"""Local HMAC trust lifecycle. Authentication is not factual truth.
Single trusted process/SQLite writer; secrets must be supplied at startup.
"""
import hashlib, hmac, json
from acquisition import PATTERN
from knowledge import atom, opposite


class Verified:
    MAX_EVIDENCE = 10000
    MAX_PROMOTIONS = 100

    def __init__(self, strategy):
        self.strategy = strategy
        self.db = strategy.db
        self.trust = {}
        self._refreshing = False
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS attestations(id TEXT PRIMARY KEY, record TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS promoted(literal TEXT PRIMARY KEY, evidence TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS trust_sources(source TEXT PRIMARY KEY, origin TEXT NOT NULL, fingerprint TEXT NOT NULL, reliability TEXT NOT NULL, active INTEGER NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS research_pending(objective TEXT PRIMARY KEY)')
        # Remove materialized attested facts before any new inference. Reload keys explicitly.
        self.strategy.knowledge.before_infer = self.refresh
        self.refresh()

    def _queue(self):
        if getattr(self.strategy, 'planner', None) is not None:
            self.db.execute('INSERT OR IGNORE INTO research_pending SELECT id FROM objectives')

    def configure(self, source, key, origin, *, reliability='qualified'):
        if (not isinstance(key, bytes) or len(key) < 32 or
            not isinstance(source, str) or not 1 <= len(source.strip()) <= 200 or
            not isinstance(origin, str) or not 1 <= len(origin.strip()) <= 200 or
            reliability not in ('qualified', 'limited')):
            raise ValueError('invalid trust configuration')
        fingerprint = hashlib.sha256(key).hexdigest()
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO trust_sources VALUES (?,?,?,?,1)', (source, origin, fingerprint, reliability))
        self.trust[source] = (key, origin)
        self.refresh()
        self.continue_research()

    def reload(self, source, key):
        """Restore a key only if it matches a persisted active source; no secret stored."""
        row = self.db.execute('SELECT origin,fingerprint,reliability,active FROM trust_sources WHERE source=?',(source,)).fetchone()
        if not row or not row[3] or not isinstance(key,bytes) or not hmac.compare_digest(hashlib.sha256(key).hexdigest(),row[1]):
            raise ValueError('key not enrolled or source revoked')
        self.configure(source,key,row[0],reliability=row[2])

    def revoke(self, source):
        with self.db:
            self.db.execute('UPDATE trust_sources SET active=0 WHERE source=?',(source,))
        self.trust.pop(source,None)
        self.refresh()
        self.continue_research()

    @staticmethod
    def payload(source, excerpt):
        return json.dumps([source,excerpt],separators=(',',':')).encode()

    def _config(self, source):
        config = self.trust.get(source)
        if not config: return None
        key, origin = config
        row = self.db.execute('SELECT origin,fingerprint,reliability,active FROM trust_sources WHERE source=?',(source,)).fetchone()
        if not row or not row[3] or origin != row[0] or not hmac.compare_digest(hashlib.sha256(key).hexdigest(),row[1]): return None
        return key,origin,row[2]

    def acquire(self, source, excerpt, signature):
        config = self._config(source) if isinstance(source,str) else None
        if not config or not isinstance(excerpt,str) or not 1 <= len(excerpt) <= 2000 or not isinstance(signature,str) or len(signature)!=64:
            raise ValueError('untrusted evidence')
        key,origin,_ = config
        if not hmac.compare_digest(hmac.new(key,self.payload(source,excerpt),hashlib.sha256).hexdigest(),signature):
            raise ValueError('invalid signature')
        r = self.strategy.acquisition.extract(excerpt,source)
        if r['status'] != 'candidate': return r
        r.update(origin=origin,signature=signature,signed_text=excerpt,authenticated=True)
        with self.db:
            # Allow a valid new signature after rotation; candidate identity is stable.
            self.db.execute('INSERT OR REPLACE INTO attestations VALUES (?,?)',(r['id'],json.dumps(r)))
        self.refresh()
        self.continue_research()
        return r

    @staticmethod
    def literal(r):
        p = 'is a' if r['predicate']=='is not a' else r['predicate']
        return ('!' if r['predicate']=='is not a' else '')+'rel_'+hashlib.sha256(json.dumps([r['subject'],p,r['object']]).encode()).hexdigest()[:60]

    def _records(self):
        rows = self.db.execute('SELECT id,record FROM attestations ORDER BY id LIMIT ?', (self.MAX_EVIDENCE+1,)).fetchall()
        if len(rows)>self.MAX_EVIDENCE: raise ValueError('evidence budget exceeded')
        result=[]
        for rid,raw in rows:
            try:
                r=json.loads(raw); config=self._config(r['source'])
                if not config: continue
                key,origin,reliability=config
                signed=r.get('signed_text',r['excerpt'])
                if not hmac.compare_digest(hmac.new(key,self.payload(r['source'],signed),hashlib.sha256).hexdigest(),r['signature']): continue
                m=PATTERN.fullmatch(signed.strip())
                if not m or m.group(0)!=r['excerpt'] or tuple(r[k] for k in ('subject','predicate','object'))!=m.groups(): continue
                expected=hashlib.sha256(json.dumps([*m.groups(),r['source'],m.group(0)],ensure_ascii=False).encode()).hexdigest()
                if expected!=rid or r['id']!=rid: continue
                result.append((r,origin,hashlib.sha256(key).hexdigest(),reliability))
            except (KeyError,TypeError,ValueError,AttributeError):
                continue
        return result

    def _assess(self,literal,records):
        support=[]; opposition=[]; origins=set(); keys=set(); limited=[]
        for r,origin,key,reliability in records:
            l=self.literal(r)
            if l==opposite(literal): opposition.append(r['id'])
            if l==literal:
                if reliability!='qualified': limited.append(r['id']); continue
                if origin not in origins and key not in keys:
                    origins.add(origin); keys.add(key); support.append(r['id'])
        return dict(support=support,opposition=opposition,limited=limited,eligible=len(support)>=2 and not opposition)

    def assess(self,literal):
        atom(literal)
        return self._assess(literal,self._records())

    def refresh(self):
        """Revalidate all approved materializations, including on every native inference."""
        if self._refreshing: return
        self._refreshing=True
        try:
            with self.db:
                before=set(self.db.execute("SELECT literal,source FROM native_facts WHERE source LIKE 'attested:%'"))
                self.db.execute("DELETE FROM native_facts WHERE source LIKE 'attested:%'")
                rows=self.db.execute('SELECT literal FROM promoted ORDER BY literal LIMIT ?', (self.MAX_PROMOTIONS+1,)).fetchall()
                try:
                    if len(rows)>self.MAX_PROMOTIONS: raise ValueError('promotion budget exceeded')
                    records=self._records()
                except ValueError:
                    self.db.execute('UPDATE promoted SET evidence=?',(json.dumps(dict(eligible=False,reason='budget_exhausted')),))
                    records=None
                after=set()
                if records is not None:
                    for (literal,) in rows:
                        report=self._assess(atom(literal),records)
                        self.db.execute('UPDATE promoted SET evidence=? WHERE literal=?',(json.dumps(report),literal))
                        if report['eligible']:
                            after.add((literal,'attested:'+literal))
                    self.db.executemany('INSERT INTO native_facts VALUES (?,?)',sorted(after))
                if before!=after: self._queue()
        finally:
            self._refreshing=False

    def promote(self,literal):
        report=self.assess(literal)
        if not report['eligible']:
            self.refresh(); return report
        with self.db:
            if not self.db.execute('SELECT 1 FROM promoted WHERE literal=?',(literal,)).fetchone() and self.db.execute('SELECT count(*) FROM promoted').fetchone()[0]>=self.MAX_PROMOTIONS:
                raise ValueError('promotion budget exceeded')
            self.db.execute('INSERT OR IGNORE INTO promoted VALUES (?,?)',(literal,json.dumps(report)))
        self.refresh()
        self.continue_research()
        return report

    def graph(self, *, limit=100):
        """Authenticated signed edges; explicit promotion status, not entailment."""
        if type(limit) is not int or not 1<=limit<=1000: raise ValueError('invalid limit')
        self.refresh()
        active={r[0] for r in self.db.execute("SELECT literal FROM native_facts WHERE source LIKE 'attested:%'")}
        rows=self._records(); edges=[]
        for r,origin,_,reliability in rows[:limit]:
            l=self.literal(r)
            edges.append(dict(subject=r['subject'],predicate=r['predicate'],object=r['object'],literal=l,evidence=r['id'],source=r['source'],origin=origin,reliability=reliability,promoted=l in active))
        return dict(edges=edges,truncated=len(rows)>limit)

    def continue_research(self,limit=8):
        """Drain durable dirty queue; includes previously resolved objectives."""
        if type(limit) is not int or not 1<=limit<=32: raise ValueError('invalid limit')
        if getattr(self.strategy,'planner',None) is None: return []
        reports=[]
        for (oid,) in self.db.execute('SELECT objective FROM research_pending ORDER BY rowid LIMIT ?',(limit,)).fetchall():
            report=self.strategy.planner.resume(oid)
            with self.db: self.db.execute('DELETE FROM research_pending WHERE objective=?',(oid,))
            reports.append(report)
        return reports
