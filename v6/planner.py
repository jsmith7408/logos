"""Local research planning over explicit literals; never authenticates evidence."""
import json, uuid
from knowledge import atom, opposite
from adjudication import evaluate

class Planner:
    def __init__(self, strategy):
        self.strategy=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS objectives(id TEXT PRIMARY KEY, question TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS investigations(id TEXT PRIMARY KEY, objective TEXT NOT NULL, report TEXT NOT NULL)')
    def create(self, question):
        if not isinstance(question,str) or not question.strip() or len(question)>256: raise ValueError('invalid objective')
        rid=str(uuid.uuid4())
        with self.db: self.db.execute('INSERT INTO objectives VALUES (?,?)',(rid,question.strip()))
        return rid
    def get(self,rid):
        row=self.db.execute('SELECT report FROM investigations WHERE id=?',(rid,)).fetchone()
        if row is None: raise KeyError(rid)
        return json.loads(row[0])
    def history(self, objective, *, limit=20):
        if type(limit) is not int or not 1<=limit<=100: raise ValueError('invalid limit')
        if self.db.execute('SELECT 1 FROM objectives WHERE id=?',(objective,)).fetchone() is None: raise KeyError(objective)
        rows=self.db.execute('SELECT report FROM investigations WHERE objective=? ORDER BY rowid DESC LIMIT ?', (objective,limit)).fetchall()
        return [json.loads(row[0]) for row in rows]
    def resume(self, objective, *, max_checks=8, inference_budget=1000):
        # Re-evaluate against current knowledge; never reuse stale proof as evidence.
        previous=self.history(objective,limit=1)
        return self.run(objective,max_checks=max_checks,inference_budget=inference_budget,
                        _previous=previous[0]['id'] if previous else None)
    def run(self, objective, *, max_checks=8, inference_budget=1000, _previous=None):
        if type(max_checks) is not int or not 1<=max_checks<=32 or type(inference_budget) is not int or not 1<=inference_budget<=10000: raise ValueError('invalid limits')
        row=self.db.execute('SELECT question FROM objectives WHERE id=?',(objective,)).fetchone()
        if row is None: raise KeyError(objective)
        q=row[0]; r=dict(id=str(uuid.uuid4()),objective=objective,question=q,authenticated=False,provider_attempts=0,checks=[],gaps=[],hypotheses=[])
        if _previous is not None: r['previous_investigation']=_previous
        try: value=str(evaluate(q))
        except (ValueError,SyntaxError,ZeroDivisionError,RecursionError): value=None
        if value is not None:
            r.update(strategy='exact_arithmetic',status='local_arithmetic_check',conclusion=value)
        else:
            try: target=atom(q)
            except ValueError: target=None
            if target is None:
                r.update(strategy='abstention',status='unsupported',conclusion=None,gaps=['structured objective required'])
            else:
                r.update(strategy='scoped_inference',conclusion=None)
                pending=[target]; seen=set()
                while pending and len(r['checks'])<max_checks:
                    x=pending.pop(0)
                    if x in seen: continue
                    seen.add(x)
                    proof=self.strategy.knowledge.infer(x,inference_budget,isolate=True)
                    status=proof['status']; r['checks'].append(proof)
                    if x==target:
                        r['status']=status
                        if status in ('supported','refuted'): r['conclusion']=status
                    if status!='unknown': continue
                    r['gaps'].append(x)
                    rules=self.db.execute('SELECT premises FROM native_rules WHERE conclusion=? ORDER BY premises LIMIT ?', (x,max_checks+1)).fetchall()
                    if len(rules)>max_checks: r['rule_scan_truncated']=True
                    for (raw,) in rules[:max_checks]:
                        premises=json.loads(raw)
                        # A candidate explanation is conditional, never a new fact.
                        if any(p in proof['proof'] for p in premises) and not any(opposite(p) in proof['proof'] for p in premises):
                            r['hypotheses'].append(dict(conclusion=x,premises=premises,status='conditional_unverified',support=[p for p in premises if p in proof['proof']]))
                        for p in premises:
                            if p not in seen and p not in pending: pending.append(p)
                r['truncated']=bool(pending) or r.get('rule_scan_truncated',False)
        with self.db: self.db.execute('INSERT INTO investigations VALUES (?,?,?)',(r['id'],objective,json.dumps(r)))
        if getattr(self.strategy,"monitor",None) is not None: self.strategy.monitor.record("research",r)
        return r
