import unittest
from core import Core
from evidence import Evidence
from test_evidence import setup

class DependencyTests(unittest.TestCase):
    def test_transitive_groups_and_no_truth_promotion(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        for source,excerpt in [('Journal A','First quote'),(' journal a ','Second quote'),('Journal B',' SECOND QUOTE '),('Journal C','Other')]:
            e.add(r,0,source,excerpt,'supports')
        result=e.inspect(r,0); d=result['dependency_analysis']
        self.assertEqual(sorted(map(len,d['groups'])),[1,3]); self.assertFalse(d['independence_established']); self.assertIsNone(result['conclusion']); c.close()
    def test_empty_and_bounded(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        self.assertEqual(e.inspect(r,0)['dependency_analysis']['candidate_group_count'],0)
        for i in range(3): e.add(r,0,'same',str(i),'unclear')
        result=e.inspect(r,0,2); self.assertTrue(result['truncated']); self.assertEqual(result['dependency_analysis']['eligible_records'],2); c.close()
