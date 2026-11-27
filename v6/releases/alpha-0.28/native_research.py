"""Native-only bounded research. No inference services, generated code, or model dependencies."""
import json, hashlib, re, uuid, random
from collections import Counter
from fractions import Fraction
from multidomain import solve, CANDIDATE, digest
from knowledge import atom

TOKEN=re.compile(r'[A-Za-z0-9_]+|[.!?]')

def rational(x):
    if type(x) is not str or len(x)>40 or not re.fullmatch(r'-?\d+(?:/[1-9]\d*)?',x): raise ValueError('rational string required')
    return Fraction(x)

def evaluate(task):
    """Typed composition. Graph path is not proof of causal effect."""
    if type(task) is not dict: raise ValueError('task required')
    d=task.get('domain')
    if d in CANDIDATE: return solve(task,CANDIDATE[d])
    if d=='probability' and set(task)=={'domain','prior','likelihood','alternative'}:
        p,a,b=map(rational,(task['prior'],task['likelihood'],task['alternative']))
        if not all(0<=v<=1 for v in (p,a,b)): raise ValueError('invalid probability')
        z=p*a+(1-p)*b
        return str(p*a/z) if z else None
    if d=='composition' and set(task)=={'domain','graph','probability'}:
        if task['graph'].get('domain')!='graph' or task['probability'].get('domain')!='probability': raise ValueError('typed inputs required')
        # Conditional scenario, not causal identification or a learned transfer.
        path=evaluate(task['graph']); p=evaluate(task['probability'])
        return {'path':path,'posterior':p,'causal_effect':'not_identified'}
    raise ValueError('unsupported native domain')

class NativeResearch:
    def __init__(self,strategy):
        self.s=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS native28_hypotheses(id TEXT PRIMARY KEY, literal TEXT UNIQUE, status TEXT, report TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS native28_runs(id TEXT PRIMARY KEY, report TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS native28_benchmarks(id TEXT PRIMARY KEY, record TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS native28_language(a TEXT,b TEXT,n INTEGER, PRIMARY KEY(a,b))')
            self.db.execute('CREATE TABLE IF NOT EXISTS native28_web(id TEXT PRIMARY KEY, record TEXT)')
    def _record(self,table,id,record):
        if table not in ('native28_runs','native28_benchmarks','native28_web'): raise ValueError('invalid table')
        with self.db:
            self.db.execute(f'INSERT OR IGNORE INTO {table} VALUES (?,?)',(id,json.dumps(record,allow_nan=False)))
            self.db.execute(f'DELETE FROM {table} WHERE rowid IN (SELECT rowid FROM {table} ORDER BY rowid DESC LIMIT -1 OFFSET 100)')
    def status(self):
        return {'third_party_ai':'disabled','native_domains':['arithmetic','logic','graph','probability','composition'],'language':'own corpus bigram, unverified','hypotheses':self.db.execute('SELECT count(*) FROM native28_hypotheses').fetchone()[0],'web':'explicit public HTTPS allowlist only','authenticated':False}
    def questions(self,limit=8):
        if type(limit) is not int or not 1<=limit<=16: raise ValueError('invalid limit')
        rows=self.db.execute('SELECT question FROM objectives ORDER BY rowid LIMIT 128').fetchall(); out=[]
        for (q,) in rows:
            try: atom(q)
            except ValueError: continue
            r=self.s.knowledge.infer(q,budget=512,isolate=True)
            if r['status'] not in ('unknown','conflict'): continue
            for (raw,) in self.db.execute('SELECT premises FROM native_rules WHERE conclusion=? ORDER BY premises LIMIT 8',(q,)):
                for p in json.loads(raw):
                    if p not in out and self.s.knowledge.infer(p,budget=512,isolate=True)['status']=='unknown': out.append(p)
                    if len(out)>=limit: return out
            if q not in out: out.append(q)
            if len(out)>=limit: break
        return out[:limit]
    def hypothesize(self,literal):
        atom(literal); key=digest(literal)
        r=self.s.knowledge.infer(literal,budget=1000,isolate=True)
        result={'id':key,'literal':literal,'status':r['status'],'authenticated':False,'promoted':False}
        with self.db:
            if not self.db.execute('SELECT 1 FROM native28_hypotheses WHERE id=?',(key,)).fetchone() and self.db.execute('SELECT count(*) FROM native28_hypotheses').fetchone()[0]>=1000: raise ValueError('hypothesis capacity')
            self.db.execute('INSERT INTO native28_hypotheses VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,report=excluded.report',(key,literal,r['status'],json.dumps(result)))
        return result
    def transfer(self,task):
        # Results are isolated scenario records; no facts, rules, or trust changes.
        result={'task':task,'result':evaluate(task),'authenticated':False,'status':'quarantined_scenario','promoted':False}
        self._record('native28_runs',digest(result),result); return result
    def import_benchmark(self,rows,source):
        if type(source) is not str or not 1<=len(source)<=512 or type(rows) is not list or not 1<=len(rows)<=120: raise ValueError('invalid benchmark')
        seen=set(); scores=[]
        for r in rows:
            if type(r) is not dict or set(r)!={'task','expected'}: raise ValueError('invalid row')
            key=digest(r['task'])
            if key in seen: raise ValueError('duplicate task')
            seen.add(key); value=evaluate(r['task']); scores.append({'task_digest':key,'result':value,'correct':value==r['expected']})
        rec={'source':source,'dataset_digest':digest(rows),'total':len(rows),'correct':sum(x['correct'] for x in scores),'outcomes':scores,'authenticated':False,'independence_verified':False,'activation':False}
        self._record('native28_benchmarks',rec['dataset_digest'],rec); return rec
    def cycle(self,seed=28112601,limit=4):
        if type(seed) is not int or not 0<=seed<2**32 or type(limit) is not int or not 1<=limit<=8: raise ValueError('invalid cycle budget')
        qs=self.questions(limit); hypotheses=[self.hypothesize(q) for q in qs]
        # Allocate extra trials to unresolved work, with an explicit cap.
        n=min(32,8+3*len(hypotheses)); rng=random.Random(seed); rows=[]
        for _ in range(n):
            a,b=rng.randint(1,9),rng.randint(1,9)
            # Equal likelihoods imply posterior equals prior (independent algebraic invariant).
            prior=str(Fraction(a,10)); likelihood=str(Fraction(b,10))
            rows.append({'task':{'domain':'probability','prior':prior,'likelihood':likelihood,'alternative':likelihood},'expected':prior})
        benchmark=self.import_benchmark(rows_unique(rows),'generated invariant; not independent')
        r={'id':str(uuid.uuid4()),'seed':seed,'stages':['question_generation','hypothesis_check','experiment','appraisal'],'questions':qs,'hypotheses':hypotheses,'allocated_trials':n,'benchmark':benchmark,'provider_attempts':0,'activated':False,'authenticated':False}
        self._record('native28_runs',r['id'],r); return r
    def train_language(self,text):
        if type(text) is not str or not 1<=len(text)<=40000: raise ValueError('bounded local corpus required')
        tokens=TOKEN.findall(text.lower()); pairs=Counter(zip(tokens,tokens[1:]))
        if len(tokens)>5000: raise ValueError('token limit')
        with self.db:
            for (a,b),n in pairs.items():
                self.db.execute('INSERT INTO native28_language VALUES (?,?,?) ON CONFLICT(a,b) DO UPDATE SET n=min(n+excluded.n,1000000)',(a,b,n))
            if self.db.execute('SELECT count(*) FROM native28_language').fetchone()[0]>20000: raise ValueError('model capacity')
        return {'tokens':len(tokens),'pairs':len(pairs),'source':'user-supplied corpus','authenticated':False}
    def predict(self,start,max_tokens=8):
        if type(start) is not str or not TOKEN.fullmatch(start) or type(max_tokens) is not int or not 1<=max_tokens<=32: raise ValueError('invalid generation')
        seq=[start.lower()]
        for _ in range(max_tokens):
            row=self.db.execute('SELECT b FROM native28_language WHERE a=? ORDER BY n DESC,b LIMIT 1',(seq[-1],)).fetchone()
            if not row: break
            seq.append(row[0])
            if row[0] in '.!?': break
        return {'text':' '.join(seq),'authenticated':False,'status':'statistical_candidate','provider_attempts':0}
    def fetch(self,url,allowed_hosts):
        from web_evidence import fetch_public
        r=fetch_public(url,allowed_hosts); self._record('native28_web',r['id'],r); return r

def rows_unique(rows):
    return list({digest(r['task']):r for r in rows}.values())
