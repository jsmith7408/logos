import unittest, threading, json, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from providers import OllamaProvider, ProviderError
from core import Core
from workflow import Workflow
from types import SimpleNamespace
class Tests(unittest.TestCase):
    def setUp(self):
        self.payload=b'{"done":true,"response":"fixture"}'; self.delay=0; self.code=200; self.requests=[]
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                owner.requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length'])))); time.sleep(owner.delay)
                try:
                    self.send_response(owner.code); self.end_headers(); self.wfile.write(owner.payload)
                except OSError: pass
            def log_message(self,*args): pass
        self.server=HTTPServer(('127.0.0.1',0),Handler); self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.provider=OllamaProvider('fixture',port=self.server.server_port,timeout=.2,max_bytes=128)
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join()
    def test_workflow(self):
        core=Core(':memory:'); self.addCleanup(core.close)
        result=Workflow(SimpleNamespace(core=core)).run(['question'],self.provider)
        self.assertEqual(result['status'],'complete'); self.assertEqual(core.search('fixture')[0]['provenance'],'unverified_provider'); self.assertEqual(self.requests[0]['options']['num_predict'],512)
    def test_size(self):
        self.payload=b'x'*129
        with self.assertRaises(ProviderError): self.provider.reason('q')
    def test_invalid(self):
        self.payload=b'{"done":false,"response":"partial"}'
        with self.assertRaises(ProviderError): self.provider.reason('q')
    def test_timeout(self):
        self.delay=.5
        with self.assertRaises(ProviderError): self.provider.reason('q')
    def test_redirect(self):
        self.code=302
        with self.assertRaises(ProviderError): self.provider.reason('q')
    def test_failure_persistence(self):
        self.code=500; core=Core(':memory:'); self.addCleanup(core.close)
        result=Workflow(SimpleNamespace(core=core)).run(['q','next'],self.provider)
        self.assertEqual(result['status'],'failed'); self.assertEqual(core.search(''),[]); self.assertEqual(len(self.requests),1)
