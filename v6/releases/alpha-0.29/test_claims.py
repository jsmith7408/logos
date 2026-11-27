import unittest,json,tempfile,urllib.request,urllib.parse
from core import Core,DemoProvider
from bridge import Application
from collective import Collective
from claims import Claims,parse,relation
import test_dashboard
class Provider:
    def __init__(self,raw): self.raw=raw
    def reason(self,q): return self.raw

def claim(p=True,scope='2026'):
    return dict(subject='A',predicate='is',object='B',scope=scope,polarity=p)
class ClaimTests(unittest.TestCase):
    def test_relations(self):
        self.assertEqual(relation(claim(),claim()),'structured_agreement')
        self.assertEqual(relation(claim(),claim(False)),'structured_opposition')
        self.assertEqual(relation(claim(),claim(False,'2025')),'undetermined')
    def test_invalid(self):
        for raw in ['[]','{}','[{}]','[1]','['*2000,'[{"subject":"a","subject":"b"}]',json.dumps([claim(1)])]:
            with self.assertRaises(ValueError): parse(raw)
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            c=Core(d+'/db'); col=Collective(Application(c,None)); r=col.run('claims',{'A':Provider(json.dumps([claim()])), 'B':Provider(json.dumps([claim(False)])), 'C':DemoProvider()}); result=Claims(col).run(r['id']); c.close()
            c=Core(d+'/db'); saved=json.loads(c.db.execute('SELECT report FROM claims').fetchone()[0]); self.assertEqual(saved,result); self.assertEqual(saved['relations'][0]['relation'],'structured_opposition'); self.assertEqual(len(saved['rejected']),1); self.assertIsNone(saved['conclusion']); self.assertFalse(saved['authenticated']); c.close()
class ClaimHTTP(unittest.TestCase):
    setUp=test_dashboard.DashboardTests.setUp
    tearDown=test_dashboard.DashboardTests.tearDown
    page=test_dashboard.DashboardTests.page
    token=test_dashboard.DashboardTests.token
    def test_dashboard(self):
        token=self.token(); c=Core(self.tmp.name+'/db'); col=Collective(Application(c,None)); r=col.run('claims',{'A':Provider(json.dumps([claim()])), 'B':Provider(json.dumps([claim(False)]))}); c.close()
        page=urllib.request.urlopen(self.url+'/claims',urllib.parse.urlencode(dict(token=token,source=r['id'])).encode()).read().decode(); self.assertIn('structured_opposition',page)
