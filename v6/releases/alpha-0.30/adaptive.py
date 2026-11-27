"""Restricted, auditable adaptation. No eval/exec, arbitrary code or premise writes."""
import ast
import inspect
import hashlib
import json
import math
import random
import uuid
from collections import deque
from pathlib import Path
from fractions import Fraction
from adjudication import evaluate
from knowledge import atom, opposite
from providers import OllamaProvider


def exact(text):
    return evaluate(text)


def normalized(text):
    if len(text)>256: raise ValueError('expression limit')
    return evaluate(text.strip())


def defective(text):
    # Negative control, never eligible for activation.
    return evaluate(text)*100


REGISTRY={'exact-v1':exact,'trim-v1':normalized}


def answer(fn,text):
    try: return str(fn(text))
    except (ValueError,SyntaxError,ZeroDivisionError,RecursionError): return None


def introspect():
    # Only inspect this known module; do not disclose absolute paths or locals.
    raw=Path(__file__).read_bytes()
    tree=ast.parse(raw)
    frame=inspect.currentframe()
    try:
        caller=frame.f_back
        return dict(source_sha256=hashlib.sha256(raw).hexdigest(),
                    functions=sorted(n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)),
                    caller=caller.f_code.co_name,line=caller.f_lineno,observational_only=True,authenticated=False)
    finally:
        del frame


class Adaptive:
    LIMIT=1000
    def __init__(self,strategy):
        self.strategy=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS adaptive_policy(slot INTEGER PRIMARY KEY CHECK(slot=1), name TEXT NOT NULL)')
            self.db.execute("INSERT OR IGNORE INTO adaptive_policy VALUES (1,'exact-v1')")
            self.db.execute('CREATE TABLE IF NOT EXISTS adaptive_history(id TEXT PRIMARY KEY, record TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS hypothesis_quarantine(id TEXT PRIMARY KEY, record TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS calibration_samples(id TEXT PRIMARY KEY, record TEXT NOT NULL)')

    def active(self):
        name=self.db.execute('SELECT name FROM adaptive_policy WHERE slot=1').fetchone()[0]
        return name if name in REGISTRY else 'exact-v1'

    def compute(self,text):
        return answer(REGISTRY[self.active()],text)

    def _insert(self,table,record):
        # Table identifiers are internal constants, never provider-supplied.
        self.db.execute(f'INSERT INTO {table} VALUES (?,?)',(record['id'],json.dumps(record,allow_nan=False)))
        self.db.execute(f'DELETE FROM {table} WHERE rowid IN (SELECT rowid FROM {table} ORDER BY rowid DESC LIMIT -1 OFFSET ?)',(self.LIMIT,))

    def recent(self,table='adaptive_history',limit=20):
        if table not in ('adaptive_history','hypothesis_quarantine','calibration_samples') or type(limit) is not int or not 1<=limit<=100: raise ValueError('invalid history request')
        return [json.loads(r[0]) for r in self.db.execute(f'SELECT record FROM {table} ORDER BY rowid DESC LIMIT ?',(limit,))]

    @staticmethod
    def cases(seed):
        # Oracle derived from operands, not either evaluator. Fixed challenge cases are public.
        rng=random.Random(seed)
        cases=[('1/0',None),('2**8',None),('__import__("os")',None),('True',None),(' '*257+'1',None),('1/3+1/6','1/2'),(' 2+3 ','5')]
        for _ in range(32):
            a,b=rng.randint(-1000,1000),rng.randint(1,1000)
            cases.extend([(f'{a}+{b}',str(a+b)),(f' {a}*{b} ',str(a*b)),(f'{a}/{b}',str(Fraction(a,b)))])
        return cases

    def experiment(self,candidate,*,activate=False,seed=20261127):
        if candidate not in (*REGISTRY,'negative-control') or type(seed) is not int or not 0<=seed<2**32 or type(activate) is not bool: raise ValueError('invalid experiment')
        old=self.active(); fn=REGISTRY.get(candidate,defective)
        cases=self.cases(seed); scores=[]
        for text,expected in cases:
            a,b=answer(REGISTRY[old],text),answer(fn,text)
            scores.append(dict(expression=text,expected=expected,baseline=a,candidate=b,baseline_correct=a==expected,candidate_correct=b==expected))
        bc=sum(x['baseline_correct'] for x in scores); cc=sum(x['candidate_correct'] for x in scores)
        regressions=sum(x['baseline_correct'] and not x['candidate_correct'] for x in scores)
        eligible=candidate in REGISTRY and cc>bc and regressions==0 and cc==len(scores)
        record=dict(id=str(uuid.uuid4()),seed=seed,baseline=old,candidate=candidate,total=len(scores),baseline_correct=bc,candidate_correct=cc,regressions=regressions,eligible=eligible,activated=bool(activate and eligible),scores=scores,authenticated=False,scope='synthetic arithmetic only')
        with self.db:
            if record['activated']: self.db.execute('UPDATE adaptive_policy SET name=? WHERE slot=1',(candidate,))
            self._insert('adaptive_history',record)
        return record

    def rollback(self):
        old=self.active(); record=dict(id=str(uuid.uuid4()),action='rollback',previous=old,restored='exact-v1',authenticated=False)
        with self.db:
            self.db.execute("UPDATE adaptive_policy SET name='exact-v1' WHERE slot=1")
            self._insert('adaptive_history',record)
        return record

    def quarantine(self,literal,*,source='manual',budget=1000):
        atom(literal)
        if source not in ('manual','local_model'): raise ValueError('invalid source')
        # A proposal is never inserted in the knowledge tables. Falsification is conditional on existing premises.
        result=self.strategy.knowledge.infer(literal,budget=budget,isolate=True)
        record=dict(id=str(uuid.uuid4()),literal=literal,source=source,status='quarantined',symbolic_status=result['status'],steps=result['steps'],authenticated=False,promoted=False)
        with self.db: self._insert('hypothesis_quarantine',record)
        return record

    def investigate(self,literal,*,local_model=None,budget=1000):
        atom(literal)
        native=self.strategy.knowledge.infer(literal,budget=budget,isolate=True)
        result=dict(native_status=native['status'],provider_attempts=0,authenticated=False)
        if native['status']!='unknown' or local_model is None: return result
        if type(local_model) is not OllamaProvider: raise ValueError('loopback Ollama only')
        raw=local_model.reason('Propose one literal only, either '+literal+' or '+opposite(literal)+'. No evidence is implied.')
        result['provider_attempts']=1
        if raw.strip() in (literal,opposite(literal)): result['proposal']=self.quarantine(raw.strip(),source='local_model',budget=budget)
        else: result['proposal_rejected']=True
        return result

    def score_prediction(self,expression,prediction,confidence):
        # Scored confidence concerns answer correctness, not truth of source claims.
        expected=str(evaluate(expression))
        if not isinstance(prediction,str) or len(prediction)>128 or type(confidence) not in (float,int) or not math.isfinite(confidence) or not 0<=confidence<=1: raise ValueError('invalid prediction')
        try: correct=Fraction(prediction)==Fraction(expected)
        except (ValueError,ZeroDivisionError): correct=False
        record=dict(id=str(uuid.uuid4()),expression=expression,prediction=prediction,expected=expected,confidence=confidence,correct=correct,authenticated=False)
        with self.db: self._insert('calibration_samples',record)
        return record

    def calibration(self):
        rows=[json.loads(r[0]) for r in self.db.execute('SELECT record FROM calibration_samples ORDER BY rowid DESC LIMIT 1000')]
        n=len(rows)
        return dict(n=n,accuracy=sum(r['correct'] for r in rows)/n if n else None,brier=sum((r['confidence']-int(r['correct']))**2 for r in rows)/n if n else None,scope='submitted arithmetic predictions; descriptive, not general calibration',authenticated=False)

    def reflect(self):
        # One bounded appraisal; no recursive retries or policy writes.
        return dict(structure=introspect(),monitor=self.strategy.monitor.report(),policy=self.active(),calibration=self.calibration(),recent_improvements=[{k:v for k,v in r.items() if k!='scores'} for r in self.recent(limit=5)],authenticated=False,observational_only=True)
