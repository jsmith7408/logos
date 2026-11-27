import json, tempfile, unittest
from unittest.mock import patch
from core import Core
from bridge import Application
from strategy import Strategy
from multidomain import DOMAINS, CANDIDATE, DEV_SEED, HOLDOUT_SEED, generate, digest, solve
from providers import OllamaProvider, ProviderError

class MultiDomainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.open()
    def open(self):
        self.c=Core(self.tmp.name+'/db'); self.s=Strategy(Application(self.c,None)); self.m=self.s.multidomain
    def tearDown(self): self.c.close(); self.tmp.cleanup()
    def test_reproducible_disjoint(self):
        for d in DOMAINS:
            a=generate(d,DEV_SEED); b=generate(d,HOLDOUT_SEED)
            self.assertEqual(digest(a),digest(generate(d,DEV_SEED)))
            self.assertFalse({digest(x['task']) for x in a}&{digest(x['task']) for x in b})
    def test_gate_restart_rollback(self):
        r=self.m.cycle(); self.assertTrue(all(x['eligible'] and not x['activated'] for x in r['rounds']))
        self.assertEqual(self.m.active('graph'),'abstain')
        r=self.m.cycle(activate=True); self.assertEqual(len(r['rounds']),3)
        self.assertTrue(all(x['activated'] and x['heldout']['regressions']==0 for x in r['rounds']))
        self.c.close(); self.open(); self.assertEqual(self.m.self_model()['policies'],CANDIDATE)
        self.assertEqual(self.m.cycle()['rounds'],[])
        self.m.rollback('graph'); self.assertEqual(self.m.active('graph'),'abstain')
    def test_recursive_bound(self):
        r=self.m.cycle(activate=True,max_rounds=1); self.assertEqual(len(r['rounds']),1); self.assertEqual(r['rounds'][0]['domain'],'graph')
        self.assertEqual(self.m.active('arithmetic'),'exact')
        with self.assertRaises(ValueError): self.m.cycle(max_rounds=4)
        with self.assertRaises(ValueError): self.m.cycle(dev_seed=1,holdout_seed=1)
    def test_reject_harmful_candidate(self):
        def broken(task,policy): return 'wrong' if policy=='trim' else solve(task,policy)
        with patch('multidomain.solve',side_effect=broken): r=self.m.cycle(activate=True)
        row=next(x for x in r['rounds'] if x['domain']=='arithmetic')
        self.assertFalse(row['eligible']); self.assertIsNone(row['heldout']); self.assertEqual(self.m.active('arithmetic'),'exact')
    def test_heldout_regression_rejected(self):
        bad=next(r['task'] for r in generate('arithmetic',HOLDOUT_SEED) if r['expected'] is not None and not r['task']['expression'].startswith(' '))
        def broken(task,policy): return 'wrong' if policy=='trim' and task==bad else solve(task,policy)
        with patch('multidomain.solve',side_effect=broken): r=self.m.cycle(activate=True)
        row=next(x for x in r['rounds'] if x['domain']=='arithmetic')
        self.assertEqual(row['development']['candidate_correct'],60); self.assertGreater(row['heldout']['regressions'],0); self.assertFalse(row['activated'])
    def test_graph_cases(self):
        t=dict(domain='graph',edges=[['A','B'],['B','C'],['C','A']],start='A',target='C')
        self.assertIsNone(self.m.solve(t)); self.m.cycle(activate=True,max_rounds=1)
        self.assertEqual(self.s.run('domain:'+json.dumps(t),native_only=True)['conclusion'],'reachable')
        t['target']='D'; self.assertEqual(self.m.solve(t),'unreachable')
        t['target']='A'; self.assertEqual(self.m.solve(t),'reachable')
    def test_logic_scenario_isolation(self):
        t=dict(domain='logic',facts=['A','X','!X'],rules=[[['A'],'B']],query='B')
        self.assertEqual(solve(t,'global'),'conflict'); self.assertEqual(solve(t,'scoped'),'supported')
        t['facts'].append('!A'); self.assertEqual(solve(t,'scoped'),'conflict')
        self.assertEqual(self.s.knowledge.infer('B')['status'],'unknown')
    def test_withdrawal_dependencies(self):
        k=self.s.knowledge; k.fact('A','one'); k.fact('A','two'); k.rule(['A'],'B'); k.rule(['B'],'C')
        oid=self.s.planner.create('C'); other=self.s.planner.create('Z'); self.s.planner.run(oid)
        r=self.m.retract_manual('A','one'); self.assertEqual(r['queued'],[oid]); self.assertEqual(k.infer('C')['status'],'supported')
        r=self.m.retract_manual('A','two'); self.assertIn('C',r['affected']); self.assertNotIn(other,r['queued']); self.assertEqual(k.infer('C')['status'],'unknown')
        self.s.verified.continue_research(); self.assertEqual(self.s.planner.history(oid)[0]['status'],'unknown')
    def test_withdrawal_budget_fail_closed(self):
        k=self.s.knowledge; k.fact('A','one'); k.rule(['A'],'B'); k.rule(['B'],'C')
        with self.assertRaises(ValueError): self.m.retract_manual('A','one',budget=1)
        self.assertEqual(k.infer('A')['status'],'supported')
        with self.assertRaises(ValueError): self.m.retract_manual('A','attested:A')
    def test_quarantine_multi(self):
        self.s.knowledge.fact('A','manual'); self.s.knowledge.fact('!B','manual'); p=OllamaProvider('mock')
        with patch.object(p,'reason',return_value='["C","!D"]') as mocked: r=self.m.hypotheses(['A','B','C','D'],local_model=p)
        self.assertEqual(mocked.call_count,1); self.assertEqual(len(r['proposals']),2); self.assertEqual([x['status'] for x in r['checks']],['supported','refuted','unknown','unknown'])
        self.assertEqual(self.s.knowledge.infer('C')['status'],'unknown'); self.assertTrue(all(not x['promoted'] for x in r['proposals']))
    def test_neural_rejections_and_native_first(self):
        p=OllamaProvider('mock'); self.s.knowledge.fact('A','manual')
        with patch.object(p,'reason',side_effect=AssertionError): self.assertEqual(self.m.hypotheses(['A'],local_model=p)['provider_attempts'],0)
        with patch.object(p,'reason',return_value='["B","INJECT"]'): self.assertTrue(self.m.hypotheses(['B'],local_model=p)['proposal_rejected'])
        with patch.object(p,'reason',side_effect=ProviderError('unavailable')): self.assertTrue(self.m.hypotheses(['B'],local_model=p)['proposal_rejected'])
        with self.assertRaises(ValueError): self.m.hypotheses(['B'],local_model=object())
    def test_calibration_and_contract(self):
        r=self.m.cycle(max_rounds=1)['rounds'][0]['calibration']; self.assertEqual(r['n'],60); self.assertAlmostEqual(r['dev_estimate'],61/62); self.assertAlmostEqual(r['brier'],(1/62)**2)
        with self.assertRaises(ValueError): self.m.solve({'domain':'graph','edges':[],'start':'A','target':'B','code':'bad'})
        with self.assertRaises(ValueError): solve({'domain':'arithmetic','expression':'1+2'},'exec')
