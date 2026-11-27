import hashlib,hmac,json,tempfile,unittest
from core import Core
from bridge import Application
from strategy import Strategy
from knowledge import Knowledge

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=self.tmp.name+'/db'
        self.open(); self.keys={'a':b'a'*32,'b':b'b'*32,'c':b'c'*32}
        self.v.configure('a',self.keys['a'],'one'); self.v.configure('b',self.keys['b'],'two')
    def open(self):
        self.c=Core(self.path); self.s=Strategy(Application(self.c,None)); self.v=self.s.verified; self.p=self.s.planner
        self.s.collective.run=lambda *a,**k:self.fail('provider invoked')
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def add(self,source,text='A is a B'):
        sig=hmac.new(self.keys[source],self.v.payload(source,text),hashlib.sha256).hexdigest()
        return self.v.acquire(source,text,sig)
    def promote(self):
        l=self.v.literal(self.add('a')); self.add('b'); self.assertTrue(self.v.promote(l)['eligible']); return l
    def test_opposition_revokes_and_resumes_resolved(self):
        l=self.promote(); self.s.knowledge.rule([l],'C'); oid=self.p.create('C'); old=self.p.run(oid)
        self.assertEqual(old['status'],'supported'); self.add('a','A is not a B'); new=self.p.history(oid)[0]
        self.assertEqual(new['status'],'unknown'); self.assertEqual(new['previous_investigation'],old['id']); self.assertEqual(self.p.get(old['id']),old)
        self.assertEqual(self.s.run('infer-local:C',native_only=True)['conclusion'],'unknown')
    def test_restart_requires_reload(self):
        l=self.promote(); self.c.close(); self.open(); self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
        with self.assertRaises(ValueError): self.v.reload('a',self.keys['b'])
        self.v.reload('a',self.keys['a']); self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
        self.v.reload('b',self.keys['b']); self.assertEqual(self.s.knowledge.infer(l)['status'],'supported')
        self.v.revoke('b'); self.c.close(); self.open()
        with self.assertRaises(ValueError): self.v.reload('b',self.keys['b'])
        self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
    def test_reliability_gate(self):
        l=self.promote(); self.v.configure('b',self.keys['b'],'two',reliability='limited')
        self.assertFalse(self.v.assess(l)['eligible']); self.assertEqual(len(self.v.assess(l)['limited']),1)
        self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
    def test_tampered_semantics_revoked(self):
        l=self.promote(); rid=self.add('a')['id']; row=json.loads(self.c.db.execute('SELECT record FROM attestations WHERE id=?',(rid,)).fetchone()[0]); row['object']='X'
        with self.c.db: self.c.db.execute('UPDATE attestations SET record=? WHERE id=?',(json.dumps(row),rid))
        self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
    def test_graph_and_whitespace(self):
        l=self.v.literal(self.add('a','  A is a B  ')); self.add('b'); self.assertTrue(self.v.promote(l)['eligible'])
        g=self.v.graph(); self.assertEqual(len(g['edges']),2); self.assertTrue(all(r['promoted'] for r in g['edges'])); self.assertTrue(self.v.graph(limit=1)['truncated'])
    def test_reserved_source(self):
        with self.assertRaises(ValueError): self.s.knowledge.fact('A','attested:A')
    def test_bounded_queue_restart(self):
        l=self.v.literal(self.add('a')); self.add('b'); ids=[self.p.create(l) for _ in range(10)]
        self.v.promote(l); self.assertEqual(self.c.db.execute('SELECT count(*) FROM research_pending').fetchone()[0],2)
        self.c.close(); self.open(); self.v.reload('a',self.keys['a']); self.v.reload('b',self.keys['b']); self.v.continue_research()
        self.assertEqual(self.c.db.execute('SELECT count(*) FROM research_pending').fetchone()[0],0)
        self.assertTrue(all(self.p.history(x)[0]['status']=='supported' for x in ids))
    def test_rotation_revokes_old_signatures(self):
        l=self.promote(); self.keys['b']=b'z'*32; self.v.configure('b',self.keys['b'],'two'); self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
        self.add('b'); self.assertEqual(self.s.knowledge.infer(l)['status'],'supported')
    def test_budget_fail_closed(self):
        l=self.promote(); self.v.MAX_EVIDENCE=1; self.assertEqual(self.s.knowledge.infer(l)['status'],'unknown')
    def test_unbound_knowledge_does_not_accept_attested_cache(self):
        l=self.promote(); self.assertEqual(Knowledge(self.c.db).infer(l)['status'],'unknown')
