import unittest,tempfile,threading,urllib.request,urllib.parse,re,urllib.error
from dashboard import serve
class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.server=serve(self.tmp.name+'/db',0); self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start(); self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()
    def page(self): return urllib.request.urlopen(self.url).read().decode()
    def post(self,**kw): return urllib.request.urlopen(self.url+'/run',urllib.parse.urlencode(kw).encode()).read().decode()
    def token(self): return re.search(r'name=token value="([^"]+)"',self.page())[1]
    def test_workflow_and_escape(self):
        page=self.post(token=self.token(),questions='<script>alert(1)</script>\nsecond',provider='demo'); self.assertIn('complete',page); self.assertIn('&lt;script&gt;',page); self.assertNotIn('<script>',page); self.assertIn('Demonstration only: second',self.page())
    def test_csrf(self):
        with self.assertRaises(urllib.error.HTTPError) as e: self.post(token='bad',questions='x',provider='demo')
        self.assertEqual(e.exception.code,403)
    def test_budget(self):
        with self.assertRaises(urllib.error.HTTPError) as e: self.post(token=self.token(),questions='x\n'*6,provider='demo')
        self.assertEqual(e.exception.code,400)
    def test_host(self):
        with self.assertRaises(urllib.error.HTTPError) as e: urllib.request.urlopen(urllib.request.Request(self.url,headers={'Host':'evil.example'}))
        self.assertEqual(e.exception.code,403)
