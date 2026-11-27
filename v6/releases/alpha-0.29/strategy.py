"""Deterministic routing, not learned intelligence. No provider calls for exact arithmetic."""
import json, uuid, time
from adjudication import evaluate
from collective import Collective
from knowledge import Knowledge
from planner import Planner
from acquisition import Acquisition
from verified import Verified
from reflection import ReflectiveMonitor
from research_scheduler import ResearchScheduler
from adaptive import Adaptive
from multidomain import MultiDomain
from native_research import NativeResearch
class Strategy:
    def __init__(self, app):
        self.collective=Collective(app); self.db=app.core.db; self.knowledge=Knowledge(self.db)
        self.planner=Planner(self)
        self.acquisition=Acquisition(self)
        self.verified=Verified(self)
        self.monitor=ReflectiveMonitor(self.db)
        self.knowledge.monitor=self.monitor
        self.collective.monitor=self.monitor
        self.scheduler=ResearchScheduler(self)
        self.adaptive=Adaptive(self)
        self.multidomain=MultiDomain(self)
        self.native=NativeResearch(self)
        with self.db: self.db.execute('CREATE TABLE IF NOT EXISTS strategies(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def run(self, question, providers=None, budget=None, *, native_only=False):
        if not isinstance(question,str) or not question.strip() or len(question)>4000: raise ValueError('invalid question')
        start=time.monotonic()
        answer=self.adaptive.compute(question)
        report=dict(id=str(uuid.uuid4()),question=question,authenticated=False,conclusion=answer)
        if question.startswith('domain:'):
            task=json.loads(question[7:])
            value=self.multidomain.solve(task)
            report.update(strategy='native_multidomain',classification='local_scenario' if value is not None else 'unsupported_native_query',conclusion=value,provider_attempts=0)
        elif question.startswith('infer-local:'):
            evidence=self.knowledge.infer(question[12:].strip(),isolate=True)
            report.update(strategy='native_scoped_inference',classification=evidence['status'],conclusion=evidence['status'],provider_attempts=0,proof=evidence)
        elif question.startswith('infer:'):
            evidence=self.knowledge.infer(question[6:].strip())
            report.update(strategy='native_inference',classification=evidence['status'],conclusion=evidence['status'],provider_attempts=0,proof=evidence)
        elif answer is not None:
            report.update(strategy='exact_arithmetic',classification='local_arithmetic_check',provider_attempts=0)
        elif native_only or providers is None:
            report.update(strategy='native_abstention',classification='unsupported_native_query',provider_attempts=0)
        else:
            source=self.collective.run(question,providers,budget=budget)
            report.update(strategy='collective',classification='unverified',source=source['id'],provider_attempts=len(source['attempts']))
        report['elapsed_seconds']=time.monotonic()-start
        with self.db: self.db.execute('INSERT INTO strategies VALUES (?,?)',(report['id'],json.dumps(report)))
        self.monitor.record("strategy",report)
        return report
