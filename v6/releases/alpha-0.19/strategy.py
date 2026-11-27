"""Deterministic routing, not learned intelligence. No provider calls for exact arithmetic."""
import json, uuid, time
from adjudication import evaluate
from collective import Collective
class Strategy:
    def __init__(self, app):
        self.collective=Collective(app); self.db=app.core.db
        with self.db: self.db.execute('CREATE TABLE IF NOT EXISTS strategies(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def run(self, question, providers=None, budget=None, *, native_only=False):
        if not isinstance(question,str) or not question.strip() or len(question)>4000: raise ValueError('invalid question')
        start=time.monotonic()
        try: answer=str(evaluate(question))
        except (ValueError,SyntaxError,ZeroDivisionError,RecursionError): answer=None
        report=dict(id=str(uuid.uuid4()),question=question,authenticated=False,conclusion=answer)
        if answer is not None:
            report.update(strategy='exact_arithmetic',classification='local_arithmetic_check',provider_attempts=0)
        elif native_only:
            report.update(strategy='native_abstention',classification='unsupported_native_query',provider_attempts=0)
        else:
            source=self.collective.run(question,providers,budget=budget)
            report.update(strategy='collective',classification='unverified',source=source['id'],provider_attempts=len(source['attempts']))
        report['elapsed_seconds']=time.monotonic()-start
        with self.db: self.db.execute('INSERT INTO strategies VALUES (?,?)',(report['id'],json.dumps(report)))
        return report
