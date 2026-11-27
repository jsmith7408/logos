import unittest,json,tempfile,urllib.request,urllib.parse
from core import Core
from bridge import Application
from collective import Collective
from claims import Claims
from evidence import Evidence
from test_claims import Provider,claim
import test_dashboard

def setup(c):
    col=Collective(Application(c,None)); raw=json.dumps([claim()]); r=col.run('claims',{'A':Provider(raw),'B':Provider(raw)}); return col,Claims(col).run(r['id'])['id']
class EvidenceTests(unittest.TestCase):
    def test_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            c=Core(d+'/db'); col,r=setup(c); e=Evidence(col); a=e.add(r,0,'source','excerpt','supports'); e.add(r,0,'source','excerpt','opposes'); c.close()
            c=Core(d+'/db'); e=Evidence(Collective(Application(c,None))); result=e.compare(r,0); self.assertTrue(result['reported_conflict']); self.assertIsNone(result['conclusion']); self.assertFalse(result['authenticated']); self.assertEqual(result['records'][1],a); c.close()
    def test_invalid(self):
        c=Core(':memory:'); col,r=setup(c); e=Evidence(col)
        for args in [('missing',0,'s','e','supports'),(r,-1,'s','e','supports'),(r,99,'s','e','supports'),(r,0,'s','e','verified'),(r,0,'s','x'*8001,'supports')]:
            with self.assertRaises(ValueError): e.add(*args)
        c.close()
class EvidenceHTTP(unittest.TestCase):
    setUp=test_dashboard.DashboardTests.setUp
    tearDown=test_dashboard.DashboardTests.tearDown
    page=test_dashboard.DashboardTests.page
    token=test_dashboard.DashboardTests.token
    def test_dashboard(self):
        token=self.token(); c=Core(self.tmp.name+'/db'); col,r=setup(c); c.close()
        page=urllib.request.urlopen(self.url+'/evidence',urllib.parse.urlencode(dict(token=token,source=r,index=0,label='source',excerpt='<script>bad</script>',stance='supports')).encode()).read().decode(); self.assertIn('user_supplied_unverified',page); self.assertNotIn('<script>bad</script>',page)
