"""Bounded observational telemetry. Never promotes evidence or changes premises."""
import json
import time
from collections import Counter

class ReflectiveMonitor:
    def __init__(self, db, *, capacity=1000):
        if type(capacity) is not int or not 1 <= capacity <= 1000:
            raise ValueError('invalid capacity')
        self.db, self.capacity = db, capacity
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS reflection_events(seq INTEGER PRIMARY KEY, created REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)')
            self._prune()

    def _prune(self):
        self.db.execute('DELETE FROM reflection_events WHERE seq IN (SELECT seq FROM reflection_events ORDER BY seq DESC LIMIT -1 OFFSET ?)', (self.capacity,))

    def record(self, kind, report):
        if kind not in ('strategy','infer','collective','research'): raise ValueError('invalid kind')
        proof=report.get('proof')
        proof=proof if isinstance(proof,dict) else {}
        summary={k:report[k] for k in ('strategy','classification','status','comparison','steps','elapsed_seconds','provider_attempts') if k in report and type(report[k]) in (str,int,float)}
        summary['status']=proof.get('status',summary.get('status'))
        if 'steps' in proof: summary['steps']=proof['steps']
        # Avoid logging raw questions, evidence excerpts, secrets or proof trees.
        if kind=='collective': summary['provider_attempts']=len(report.get('attempts',[]))
        summary={k:v[:100] if isinstance(v,str) else v for k,v in summary.items()}
        summary['authenticated']=False
        with self.db:
            self.db.execute('INSERT INTO reflection_events(created,kind,payload) VALUES (?,?,?)',(time.time(),kind,json.dumps(summary,allow_nan=False)))
            self._prune()

    def report(self, limit=100):
        if type(limit) is not int or not 1<=limit<=1000: raise ValueError('invalid limit')
        rows=self.db.execute('SELECT created,kind,payload FROM reflection_events ORDER BY seq DESC LIMIT ?', (limit,)).fetchall()
        events=[dict(created=t,kind=k,**json.loads(p)) for t,k,p in rows]
        conflicts=[e for e in events if e.get('status')=='conflict' or e.get('classification')=='conflict']
        exhausted=[e for e in events if e.get('status')=='budget_exhausted']
        native=[e for e in events if e['kind']=='strategy' and e.get('strategy','').startswith(('native_','exact_'))]
        return dict(authenticated=False,observational_only=True,event_count=len(events),
                    period=[rows[-1][0],rows[0][0]] if rows else None,
                    strategy_distribution=dict(Counter(e.get('strategy','unknown') for e in events if e['kind']=='strategy')),
                    conflict_count=len(conflicts),budget_exhaustion_count=len(exhausted),
                    native_provider_attempts=sum(e.get('provider_attempts',0) for e in native),
                    collective_disagreements=sum(e.get('comparison')=='text_difference' for e in events),
                    recent=events[:20],notes=['Observations are not evidence; review conflicts and budget exhaustion before changing knowledge.'])
