"""Alpha 0.27: bounded, local multi-domain experiments. No generated code execution."""
import hashlib
import json
import random
import sqlite3
import uuid
from collections import deque
from fractions import Fraction
from adaptive import answer, exact, normalized
from knowledge import Knowledge, atom, opposite
from providers import OllamaProvider, ProviderError

DOMAINS=('arithmetic','logic','graph')
BASE={'arithmetic':'exact','logic':'global','graph':'abstain'}
CANDIDATE={'arithmetic':'trim','logic':'scoped','graph':'bfs'}
DEV_SEED=27112601
HOLDOUT_SEED=27112602


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate(task):
    if not isinstance(task,dict) or task.get('domain') not in DOMAINS: raise ValueError('invalid domain')
    d=task['domain']
    if d=='arithmetic':
        if set(task)!= {'domain','expression'} or not isinstance(task['expression'],str) or len(task['expression'])>256: raise ValueError('invalid expression')
    elif d=='logic':
        if set(task)!= {'domain','facts','rules','query'} or type(task['facts']) is not list or len(task['facts'])>32 or type(task['rules']) is not list or len(task['rules'])>32: raise ValueError('invalid logic task')
        atom(task['query'])
        for f in task['facts']: atom(f)
        for r in task['rules']:
            if type(r) is not list or len(r)!=2 or type(r[0]) is not list or not 1<=len(r[0])<=8: raise ValueError('invalid rule')
            for p in r[0]: atom(p)
            atom(r[1])
    else:
        if set(task)!= {'domain','edges','start','target'} or type(task['edges']) is not list or len(task['edges'])>64: raise ValueError('invalid graph task')
        atom(task['start']); atom(task['target'])
        for e in task['edges']:
            if type(e) is not list or len(e)!=2: raise ValueError('invalid edge')
            for x in e: atom(x)
    return d


def solve(task,policy):
    d=validate(task)
    if policy not in (BASE[d],CANDIDATE[d]): raise ValueError('unregistered strategy')
    if d=='arithmetic': return answer(exact if policy=='exact' else normalized,task['expression'])
    if d=='logic':
        # Isolated temporary fixture, never writes hypothetical premises into research DB.
        db=sqlite3.connect(':memory:')
        try:
            k=Knowledge(db)
            for f in task['facts']: k.fact(f,'scenario')
            for p,c in task['rules']: k.rule(p,c)
            return k.infer(task['query'],budget=10000,isolate=policy=='scoped')['status']
        finally: db.close()
    if policy=='abstain': return None
    edges={}
    for a,b in task['edges']: edges.setdefault(a,set()).add(b)
    pending=deque([task['start']]); seen={task['start']}
    while pending:
        n=pending.popleft()
        if n==task['target']: return 'reachable'
        for nxt in sorted(edges.get(n,())):
            if nxt not in seen: seen.add(nxt); pending.append(nxt)
    return 'unreachable'


def generate(domain,seed,n=60):
    """Construction-based logic labels; graph labels via transitive closure, not BFS."""
    if domain not in DOMAINS or type(seed) is not int or not 0<=seed<2**32 or type(n) is not int or not 12<=n<=120: raise ValueError('invalid generation limits')
    rng=random.Random(seed); rows=[]
    for i in range(n):
        if domain=='arithmetic':
            a,b=rng.randint(-999999,999999),rng.randint(1,999999)
            op=i%5
            e,v=[(f'{a}+{b}',a+b),(f' {a}*{b} ',a*b),(f'{a}/{b}',Fraction(a,b)),(f'({a}-{b})*2',(a-b)*2),(f' {a}/0 ',None)][op]
            task=dict(domain=domain,expression=e); expected=None if v is None else str(v)
        elif domain=='logic':
            # Disjoint symbols across cases and splits. Query-local inference contract.
            a,b,c,x=[f'{v}{seed}_{i}' for v in 'ABCX']; q=c; rules=[[[a],b],[[b],c]]
            mode=i%6
            facts,expected=([a],'supported') if mode==0 else ([a,x,'!'+x],'supported') if mode==1 else ([a,'!'+b],'conflict') if mode==2 else (['!'+c],'refuted') if mode==3 else ([b],'supported') if mode==4 else ([x],'unknown')
            task=dict(domain=domain,facts=facts,rules=rules,query=q)
        else:
            nodes=[f'N{seed}_{i}_{j}' for j in range(6)]
            edges=[[a,b] for a in nodes for b in nodes if a!=b and rng.random()<.2]
            a,b=rng.sample(nodes,2)
            if i%10==0: b=a
            reach={(x,x) for x in nodes}|{tuple(e) for e in edges}
            for k in nodes:
                for x in nodes:
                    for y in nodes:
                        if (x,k) in reach and (k,y) in reach: reach.add((x,y))
            expected='reachable' if (a,b) in reach else 'unreachable'
            task=dict(domain=domain,edges=edges,start=a,target=b)
        rows.append(dict(task=task,expected=expected))
    return rows


def compare(domain,rows,baseline,candidate):
    outcomes=[]
    for r in rows:
        a,b=solve(r['task'],baseline),solve(r['task'],candidate); y=r['expected']
        outcomes.append(dict(**r,baseline=a,candidate=b,baseline_correct=a==y,candidate_correct=b==y))
    return dict(total=len(rows),baseline_correct=sum(r['baseline_correct'] for r in outcomes),candidate_correct=sum(r['candidate_correct'] for r in outcomes),regressions=sum(r['baseline_correct'] and not r['candidate_correct'] for r in outcomes),outcomes=outcomes)


def calibrate(dev,held):
    # Single-bin empirical estimate with Laplace smoothing; not a general calibrated model.
    p=(dev['candidate_correct']+1)/(dev['total']+2)
    ys=[int(r['candidate_correct']) for r in held['outcomes']]
    rate=sum(ys)/len(ys)
    return dict(dev_estimate=p,held_accuracy=rate,brier=sum((p-y)**2 for y in ys)/len(ys),absolute_calibration_gap=abs(p-rate),n=len(ys),scope='synthetic single-bin estimate')


class MultiDomain:
    def __init__(self,strategy):
        self.strategy=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS multi_policy(domain TEXT PRIMARY KEY, policy TEXT NOT NULL)')
            self.db.executemany('INSERT OR IGNORE INTO multi_policy VALUES (?,?)',BASE.items())
            self.db.execute('CREATE TABLE IF NOT EXISTS multi_history(seq INTEGER PRIMARY KEY, record TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS multi_proposals(seq INTEGER PRIMARY KEY, record TEXT NOT NULL)')

    def active(self,domain):
        if domain not in DOMAINS: raise ValueError('invalid domain')
        p=self.db.execute('SELECT policy FROM multi_policy WHERE domain=?',(domain,)).fetchone()[0]
        return p if p in (BASE[domain],CANDIDATE[domain]) else BASE[domain]

    def _save(self,table,record,limit=100):
        self.db.execute(f'INSERT INTO {table}(record) VALUES (?)',(json.dumps(record,allow_nan=False),))
        self.db.execute(f'DELETE FROM {table} WHERE seq IN (SELECT seq FROM {table} ORDER BY seq DESC LIMIT -1 OFFSET ?)',(limit,))

    def recent(self,limit=5):
        if type(limit) is not int or not 1<=limit<=20: raise ValueError('invalid limit')
        return [json.loads(r[0]) for r in self.db.execute('SELECT record FROM multi_history ORDER BY seq DESC LIMIT ?',(limit,))]

    def solve(self,task):
        d=validate(task); return solve(task,self.active(d))

    def cycle(self,*,activate=False,max_rounds=3,dev_seed=DEV_SEED,holdout_seed=HOLDOUT_SEED):
        if type(activate) is not bool or type(max_rounds) is not int or not 1<=max_rounds<=3 or dev_seed==holdout_seed: raise ValueError('invalid cycle')
        # Both sets are generated once. The fixed candidate is selected on development only.
        datasets={d:(generate(d,dev_seed),generate(d,holdout_seed)) for d in DOMAINS}
        for d,(dev,held) in datasets.items():
            if {digest(r['task']) for r in dev}&{digest(r['task']) for r in held}: raise ValueError('development/holdout overlap')
        record=dict(id=str(uuid.uuid4()),dev_seed=dev_seed,holdout_seed=holdout_seed,rounds=[],authenticated=False,scope='local synthetic distinct-seed evaluation; not external independent validation')
        seen=set()
        for _ in range(max_rounds):
            # Autonomous weakness ranking from measured development errors only.
            ranked=[]
            for d in DOMAINS:
                if d in seen: continue
                old=self.active(d); dev,held=datasets[d]
                trial=compare(d,dev,old,CANDIDATE[d])
                ranked.append((trial['total']-trial['baseline_correct'],d,old,trial))
            if not ranked: break
            errors,d,old,trial=max(ranked,key=lambda r:(r[0],r[1]))
            if errors==0: break
            seen.add(d); dev,held=datasets[d]
            selected=trial['candidate_correct']>trial['baseline_correct'] and trial['regressions']==0
            # Do not evaluate an unselected candidate against holdout.
            validation=compare(d,held,old,CANDIDATE[d]) if selected else None
            eligible=bool(validation and validation['regressions']==0 and validation['candidate_correct']>validation['baseline_correct'] and validation['candidate_correct']==validation['total'] and trial['candidate_correct']==trial['total'])
            r=dict(domain=d,weakness_count=errors,baseline=old,candidate=CANDIDATE[d],dev_digest=digest(dev),heldout_digest=digest(held),development=trial,heldout=validation,eligible=eligible,activated=bool(activate and eligible),calibration=calibrate(trial,validation) if validation else None)
            record['rounds'].append(r)
        # Activation and audit record share one transaction; single trusted writer.
        with self.db:
            for r in record['rounds']:
                if r['activated']:
                    cursor=self.db.execute('UPDATE multi_policy SET policy=? WHERE domain=? AND policy=?',(r['candidate'],r['domain'],r['baseline']))
                    if cursor.rowcount!=1: raise RuntimeError('policy changed; retry')
            self._save('multi_history',record)
        return record

    def rollback(self,domain):
        old=self.active(domain); record=dict(id=str(uuid.uuid4()),action='rollback',domain=domain,previous=old,restored=BASE[domain],authenticated=False)
        with self.db:
            self.db.execute('UPDATE multi_policy SET policy=? WHERE domain=?',(BASE[domain],domain)); self._save('multi_history',record)
        return record

    def hypotheses(self,literals,*,local_model=None,budget=1000):
        if type(literals) is not list or not 1<=len(literals)<=8: raise ValueError('invalid hypotheses')
        literals=list(dict.fromkeys(map(atom,literals)))
        checks=[self.strategy.knowledge.infer(x,budget,isolate=True) for x in literals]
        unresolved=[r['query'] for r in checks if r['status']=='unknown']
        result=dict(id=str(uuid.uuid4()),checks=[dict(literal=r['query'],status=r['status']) for r in checks],proposals=[],provider_attempts=0,authenticated=False)
        if unresolved and local_model is not None:
            if type(local_model) is not OllamaProvider: raise ValueError('loopback Ollama only')
            allowed=set(unresolved)|{opposite(x) for x in unresolved}
            result['provider_attempts']=1
            try:
                raw=local_model.reason('Return JSON array of at most 8 distinct candidate literals from this exact set only: '+json.dumps(sorted(allowed)))
                if len(raw)>2048: raise ValueError('oversized proposal')
                proposed=json.loads(raw)
                if type(proposed) is not list or not 1<=len(proposed)<=8 or any(type(x) is not str or x not in allowed for x in proposed) or len(set(proposed))!=len(proposed): raise ValueError('invalid proposal')
                result['proposals']=[self.strategy.adaptive.quarantine(x,source='local_model',budget=budget) for x in proposed]
            except (ProviderError,ValueError,TypeError): result['proposal_rejected']=True
        with self.db: self._save('multi_proposals',result)
        return result

    def retract_manual(self,literal,source,*,budget=1000):
        """Explicit source-specific withdrawal; derive transitive dependents, never delete derived rules."""
        atom(literal)
        if not isinstance(source,str) or not source.strip() or len(source)>1000 or source.lower().startswith('attested:') or type(budget) is not int or not 1<=budget<=1000: raise ValueError('invalid withdrawal')
        rules=self.db.execute('SELECT premises,conclusion FROM native_rules LIMIT ?',(budget+1,)).fetchall()
        objectives=self.db.execute('SELECT id,question FROM objectives LIMIT ?',(budget+1,)).fetchall()
        if len(rules)>budget or len(objectives)>budget: raise ValueError('revision budget exceeded')
        affected={literal,opposite(literal)}; steps=0
        while True:
            n=len(affected)
            for p,c in rules:
                steps+=1
                if steps>budget: raise ValueError('revision budget exceeded')
                if affected.intersection(json.loads(p)): affected.update((c,opposite(c)))
            if n==len(affected): break
        with self.db:
            removed=self.db.execute('DELETE FROM native_facts WHERE literal=? AND source=?',(literal,source)).rowcount
            queued=[oid for oid,q in objectives if q in affected] if removed else []
            self.db.executemany('INSERT OR IGNORE INTO research_pending VALUES (?)',((oid,) for oid in queued))
            record=dict(id=str(uuid.uuid4()),action='manual_withdrawal',literal=literal,source=source,removed=removed,affected=sorted(affected),queued=queued,authenticated=False)
            self._save('multi_history',record)
        return record

    def self_model(self):
        # Persistent state is policy/history; no subjective self-awareness claim.
        latest=[]
        for r in self.recent():
            latest.append({**{k:v for k,v in r.items() if k!='rounds'},'rounds':[dict(domain=x['domain'],eligible=x['eligible'],activated=x['activated'],calibration=x['calibration']) for x in r.get('rounds',[])]})
        return dict(policies={d:self.active(d) for d in DOMAINS},recent=latest,monitor=self.strategy.monitor.report(limit=20),authenticated=False,observational_only=True)
