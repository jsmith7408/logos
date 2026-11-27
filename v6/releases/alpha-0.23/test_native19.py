import unittest,tempfile,json
from core import Core
from bridge import Application
from strategy import Strategy
from collective import Collective
from claims import Claims
from test_claims import Provider,claim
class NativeTests(unittest.TestCase):
    def test_native_never_calls_provider(self):
        with tempfile.TemporaryDirectory() as d:
            c=Core(d+'/db'); s=Strategy(Application(c,None))
            def forbidden(*a,**k): raise AssertionError('provider called')
            s.collective.run=forbidden
            self.assertEqual(s.run('2+3',native_only=True)['conclusion'],'5')
            r=s.run('Explain gravity',native_only=True)
            self.assertIsNone(r['conclusion']); self.assertEqual(r['provider_attempts'],0)
            c.close()
    def test_duplicate_claims(self):
        with tempfile.TemporaryDirectory() as d:
            c=Core(d+'/db'); col=Collective(Application(c,None))
            r=col.run('claims',{'A':Provider(json.dumps([claim(),claim(),claim(False)])), 'B':Provider(json.dumps([claim()]))})
            report=Claims(col).run(r['id'])
            self.assertEqual(len(report['claims']),3); self.assertEqual(len(report['duplicates']),1)
            self.assertEqual(len(report['relations']),2); self.assertFalse(report['authenticated']); c.close()
