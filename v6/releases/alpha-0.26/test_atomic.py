import unittest,tempfile,sqlite3
from core import Core,DemoProvider
from bridge import Application
from workflow import Workflow
class AtomicTests(unittest.TestCase):
 def setUp(self):
    t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.c=Core(t.name+'/db'); self.addCleanup(self.c.close); self.w=Workflow(Application(self.c,None))
 def test_rollback(self):
    self.c.db.execute("CREATE TRIGGER reject_step BEFORE UPDATE ON steps WHEN NEW.status='complete' BEGIN SELECT RAISE(ABORT,'injected'); END")
    with self.assertRaises(sqlite3.IntegrityError): self.w.run(['a'],DemoProvider())
    self.assertEqual(self.c.search(''),[])
    self.assertEqual(self.w.recover_interrupted(),1)
    rid=self.c.db.execute('SELECT id FROM runs').fetchone()[0]
    self.assertEqual(self.w.status(rid)['steps'][0]['status'],'interrupted')
    self.assertEqual(self.w.recover_interrupted(),0)
 def test_final_atomic(self):
    self.c.db.execute("CREATE TRIGGER reject_run BEFORE UPDATE ON runs WHEN NEW.status='complete' BEGIN SELECT RAISE(ABORT,'injected'); END")
    with self.assertRaises(sqlite3.IntegrityError): self.w.run(['a','b'],DemoProvider())
    self.assertEqual(len(self.c.search('')),1)
    self.w.recover_interrupted()
    rid=self.c.db.execute('SELECT id FROM runs').fetchone()[0]
    self.assertEqual([s['status'] for s in self.w.status(rid)['steps']],['complete','interrupted'])
 def test_recovery_preserves_completed(self):
    r=self.w.run(['a'],DemoProvider()); self.assertEqual(self.w.recover_interrupted(),0); self.assertEqual(self.w.status(r['id']),r)
