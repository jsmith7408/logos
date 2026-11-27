"""Single-user, explicitly ticked native research queue. No background daemon."""
import math
import time
import uuid

class ResearchScheduler:
    def __init__(self, strategy):
        self.strategy=strategy; self.db=strategy.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS native_jobs(id TEXT PRIMARY KEY, objective TEXT NOT NULL UNIQUE, interval INTEGER NOT NULL, due REAL NOT NULL, active INTEGER NOT NULL, priority INTEGER NOT NULL)')

    def schedule(self, objective, *, interval=3600, priority=0, now=None):
        if type(interval) is not int or not 60<=interval<=2592000 or type(priority) is not int or not 0<=priority<=10: raise ValueError('invalid schedule')
        now=self._time(now)
        self.strategy.planner.history(objective,limit=1)
        if self.db.execute('SELECT 1 FROM native_jobs WHERE objective=?',(objective,)).fetchone(): raise ValueError('objective already scheduled')
        if self.db.execute('SELECT count(*) FROM native_jobs').fetchone()[0]>=1000: raise ValueError('job capacity exceeded')
        jid=str(uuid.uuid4())
        with self.db: self.db.execute('INSERT INTO native_jobs VALUES (?,?,?,?,1,?)',(jid,objective,interval,now,priority))
        return jid

    @staticmethod
    def _time(now):
        now=time.time() if now is None else now
        if type(now) not in (int,float) or not math.isfinite(now) or not 0<=now<=1e11: raise ValueError('invalid time')
        return now

    def cancel(self, jid):
        with self.db: self.db.execute('UPDATE native_jobs SET active=0 WHERE id=?',(jid,))

    def tick(self, *, now=None, limit=4, max_checks=8, inference_budget=1000):
        now=self._time(now)
        if type(limit) is not int or not 1<=limit<=8: raise ValueError('invalid limit')
        rows=self.db.execute('SELECT id,objective,interval FROM native_jobs WHERE active=1 AND due<=? ORDER BY priority DESC,due,id LIMIT ?', (now,limit)).fetchall()
        results=[]
        for jid,oid,interval in rows:
            report=self.strategy.planner.resume(oid,max_checks=max_checks,inference_budget=inference_budget)
            with self.db: self.db.execute('UPDATE native_jobs SET due=? WHERE id=?',(now+interval,jid))
            results.append(dict(job=jid,report=report))
        return results
