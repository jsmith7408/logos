"""Bounded comparison of provider outputs, not a truth adjudicator."""
import json, uuid, time, math
from worker import DeadlineProvider
from core import DemoProvider

class Collective:
    def __init__(self, app):
        self.app=app; self.db=app.core.db; self.monitor=None
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS collective(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def run(self, question, providers, budget=None):
        if not isinstance(question,str) or not question.strip() or len(question)>4000: raise ValueError('invalid question')
        if not isinstance(providers,dict) or not 2<=len(providers)<=5 or any(not isinstance(k,str) or not k.strip() or len(k)>100 for k in providers): raise ValueError('invalid provider roster')
        if len({id(p) for p in providers.values()})!=len(providers): raise ValueError('duplicate provider instance')
        if budget is not None:
            if type(budget) not in (int,float) or not math.isfinite(budget) or not 0<budget<=300: raise ValueError('invalid budget')
            if any(type(p) not in (DeadlineProvider,DemoProvider) for p in providers.values()): raise ValueError('budget requires bounded providers')
        end=time.monotonic()+budget if budget is not None else None
        report=dict(roster=list(providers),id=str(uuid.uuid4()),question=question,status='running',attempts=[],classification='unverified',conclusion=None)
        with self.db: self.db.execute('INSERT INTO collective VALUES (?,?)',(report['id'],json.dumps(report)))
        answers=[]
        for label,provider in providers.items():
            try:
                if end is not None:
                    remaining=end-time.monotonic()
                    if remaining<=0: raise TimeoutError('aggregate budget exhausted')
                    if type(provider) is DeadlineProvider: provider=DeadlineProvider(provider.provider,min(provider.deadline,remaining))
                record=self.app.core.prepare(question,provider)
                if len(record['result'])>65536: raise ValueError('response too large')
            except Exception as exc:
                report['attempts'].append(dict(provider=label,error=type(exc).__name__))
                with self.db: self._save(report)
                continue
            report['attempts'].append(dict(provider=label,record=record['id'],provenance=record['provenance']))
            answers.append(record['result'])
            with self.db:
                self.app.core.insert(record); self._save(report)
        report['status']='complete' if len(answers)==len(providers) else 'partial'
        report['comparison']='insufficient' if len(answers)<2 else 'exact_agreement' if len(set(answers))==1 else 'text_difference'
        with self.db: self._save(report)
        if self.monitor is not None: self.monitor.record("collective",report)
        return report
    def _save(self,report):
        self.db.execute('UPDATE collective SET report=? WHERE id=?',(json.dumps(report),report['id']))
    def get(self,rid):
        row=self.db.execute('SELECT report FROM collective WHERE id=?',(rid,)).fetchone()
        if row is None: raise KeyError(rid)
        return json.loads(row[0])

    def recover_interrupted(self):
        """Offline only: stop all writers before calling. Never replay inference."""
        recovered=[]
        with self.db:
            for (raw,) in self.db.execute('SELECT report FROM collective').fetchall():
                report=json.loads(raw)
                if report['status']!='running': continue
                report['status']='interrupted'
                report['comparison']='unfinished'
                self._save(report); recovered.append(report['id'])
        return recovered
