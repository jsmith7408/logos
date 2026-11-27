"""Regression checks for Alpha 0.16 evidence inspection."""
import json, sqlite3, tempfile, unittest, urllib.parse, urllib.request
from core import Core
from bridge import Application
from collective import Collective
from evidence import Evidence
from test_evidence import setup
import test_dashboard

class EvidenceIntegrity(unittest.TestCase):
    def test_repeated_and_conflicting_evidence_is_not_authentication(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        e.add(r,0,'Journal A','quoted claim','supports')
        e.add(r,0,'Journal A','quoted claim','supports')
        e.add(r,0,'Journal B','other quotation','opposes')
        a=e.inspect(r,0)
        self.assertEqual(a['repeated_snapshots'],1)
        self.assertTrue(a['reported_conflict'])
        self.assertEqual(a['integrity_failures'],0)
        self.assertFalse(a['authenticated'])
        self.assertIsNone(a['conclusion']); c.close()

    def test_tampered_digest_and_claim_detected(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        a=e.add(r,0,'source','excerpt','supports')
        tampered=dict(a); tampered['snapshot']=dict(a['snapshot'],excerpt='modified')
        with c.db:c.db.execute('UPDATE evidence SET report=? WHERE id=?',(json.dumps(tampered),a['id']))
        self.assertEqual(e.inspect(r,0)['integrity_failures'],1)
        self.assertFalse(e.inspect(r,0)['reported_conflict'])
        tampered['sha256']='deliberately_invalid'
        tampered['snapshot']['claim']={'incorrect':'claim'}
        with c.db:c.db.execute('UPDATE evidence SET report=? WHERE id=?',(json.dumps(tampered),a['id']))
        self.assertEqual(e.inspect(r,0)['stale_claim_snapshots'],1)
        c.close()

    def test_rejects_invalid_scope_and_bounded_pagination(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        for i in range(4): e.add(r,0,'source',str(i),'unclear')
        small=e.inspect(r,0,2)
        self.assertTrue(small['truncated']); self.assertEqual(len(small['records']),2)
        for index,limit in [(-1,2),(0,0),(0,101),(False,2),(0,True)]:
            with self.assertRaises(ValueError): e.inspect(r,index,limit)
        c.close()

class EvidenceIntegrityHTTP(unittest.TestCase):
    setUp=test_dashboard.DashboardTests.setUp
    tearDown=test_dashboard.DashboardTests.tearDown
    page=test_dashboard.DashboardTests.page
    token=test_dashboard.DashboardTests.token
    def test_dashboard_inspect_escapes_and_requires_token(self):
        token=self.token(); c=Core(self.tmp.name+'/db'); col,r=setup(c)
        Evidence(col).add(r,0,'<script>source</script>','payload','supports'); c.close()
        post=urllib.parse.urlencode(dict(token=token,source=r,index=0)).encode()
        response=urllib.request.urlopen(self.url+'/evidence-inspect',post).read().decode()
        self.assertIn('fingerprint_matches',response)
        self.assertNotIn('<script>source</script>',response)
        with self.assertRaises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(self.url+'/evidence-inspect',urllib.parse.urlencode(dict(token='fake',source=r,index=0)).encode())
        self.assertEqual(exc.exception.code,403)
