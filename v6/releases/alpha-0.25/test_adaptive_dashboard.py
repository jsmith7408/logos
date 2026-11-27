import unittest, urllib.request, urllib.parse, urllib.error, json, sqlite3
import test_dashboard

class AdaptiveDashboardTests(unittest.TestCase):
    setUp=test_dashboard.DashboardTests.setUp
    tearDown=test_dashboard.DashboardTests.tearDown
    page=test_dashboard.DashboardTests.page
    token=test_dashboard.DashboardTests.token
    def submit(self,question,token=None):
        return urllib.request.urlopen(self.url+'/adaptive',urllib.parse.urlencode(dict(token=self.token() if token is None else token,questions=question,provider='demo')).encode()).read().decode()
    def reports(self):
        with sqlite3.connect(self.tmp.name+'/db') as db:
            return [json.loads(r[0]) for r in db.execute('SELECT report FROM strategies')]
    def test_exact(self):
        page=self.submit('1/3+1/6'); r=self.reports()[0]
        self.assertEqual(r['conclusion'],'1/2'); self.assertEqual(r['provider_attempts'],0); self.assertFalse(r['authenticated']); self.assertIn('exact_arithmetic',page)
    def test_fallback(self):
        page=self.submit('<script>unknown</script>'); r=self.reports()[0]
        self.assertEqual(r['provider_attempts'],2); self.assertIsNone(r['conclusion']); self.assertEqual(r['classification'],'unverified'); self.assertNotIn('<script>',page); self.assertIn('&lt;script&gt;',page)
    def test_csrf(self):
        self.page()  # initialize schema before testing rejected write
        with self.assertRaises(urllib.error.HTTPError) as e: self.submit('1+1','wrong')
        self.assertEqual(e.exception.code,403); self.assertEqual(self.reports(),[])
