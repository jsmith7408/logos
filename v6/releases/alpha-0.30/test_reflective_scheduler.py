import tempfile, unittest
from core import Core, DemoProvider
from bridge import Application
from strategy import Strategy
from reflection import ReflectiveMonitor

class ReflectiveSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'; self.open()
    def open(self):
        self.c=Core(self.path); self.s=Strategy(Application(self.c,None))
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def test_actual_native_and_conflict(self):
        self.s.knowledge.fact('A','x'); self.s.knowledge.fact('!A','y')
        self.s.run('infer:A',native_only=True); self.s.run('2+3',native_only=True)
        r=self.s.monitor.report(); self.assertEqual(r['conflict_count'],2); self.assertEqual(r['native_provider_attempts'],0); self.assertFalse(r['authenticated'])
        self.assertEqual(self.c.db.execute('SELECT count(*) FROM native_facts').fetchone()[0],2)
    def test_bound_and_no_raw_content(self):
        m=ReflectiveMonitor(self.c.db,capacity=3)
        for i in range(10): m.record('strategy',{'strategy':'test','question':'SECRET','status':'budget_exhausted'})
        r=m.report(); self.assertEqual(r['event_count'],3); self.assertEqual(r['budget_exhaustion_count'],3); self.assertNotIn('SECRET',str(r))
        with self.assertRaises(ValueError): m.report(-1)
    def test_collective_hook(self):
        self.s.collective.run('test',{'a':DemoProvider(),'b':DemoProvider()})
        self.assertEqual(self.s.monitor.report()['recent'][0]['kind'],'collective')
    def test_restart_scheduler(self):
        oid=self.s.planner.create('A'); self.s.scheduler.schedule(oid,interval=60,now=100)
        self.c.close(); self.open(); r=self.s.scheduler.tick(now=100)
        self.assertEqual(r[0]['report']['status'],'unknown'); self.assertEqual(self.s.scheduler.tick(now=159),[])
        self.s.knowledge.fact('A','local'); self.assertEqual(self.s.scheduler.tick(now=160)[0]['report']['status'],'supported')
        self.assertEqual(len(self.s.planner.history(oid)),2)
    def test_priority_and_cancel(self):
        a=self.s.planner.create('A'); b=self.s.planner.create('B'); sa=self.s.scheduler.schedule(a,now=0); sb=self.s.scheduler.schedule(b,priority=10,now=0)
        self.assertEqual(self.s.scheduler.tick(now=0,limit=1)[0]['job'],sb); self.s.scheduler.cancel(sa); self.assertEqual(self.s.scheduler.tick(now=1),[])
    def test_native_falsification(self):
        self.s.knowledge.fact('!A','local'); oid=self.s.planner.create('A'); self.s.scheduler.schedule(oid,now=0)
        self.assertEqual(self.s.scheduler.tick(now=0)[0]['report']['status'],'refuted')
    def test_research_hook(self):
        oid=self.s.planner.create('2+3'); self.s.planner.run(oid); self.assertEqual(self.s.monitor.report()['recent'][0]['kind'],'research')
