import unittest,time,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from types import SimpleNamespace
from core import Core
from workflow import Workflow
from providers import OllamaProvider,ProviderError
from worker import DeadlineProvider
class WorkerTests(unittest.TestCase):
    def setUp(self):
        owner=self; self.slow=False; self.calls=0
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                owner.calls+=1
                self.rfile.read(int(self.headers['Content-Length']))
                try:
                    if owner.slow:
                        for b in b'HTTP/1.0 200 OK\r\n':
                            self.wfile.write(bytes([b])); self.wfile.flush(); time.sleep(.1)
                    else: self.send_response(200); self.end_headers(); self.wfile.write(b'{"done":true,"response":"fixture"}')
                except OSError: pass
            def log_message(self,*args): pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.adapter=OllamaProvider('fixture',port=self.server.server_port,timeout=5)
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join()
    def test_success(self): self.assertEqual(DeadlineProvider(self.adapter,3).reason('q'),'fixture')
    def test_slow_headers(self):
        self.slow=True; start=time.monotonic()
        with self.assertRaisesRegex(ProviderError,'deadline'): DeadlineProvider(self.adapter,1.0).reason('q')
        self.assertLess(time.monotonic()-start,3)
    def test_workflow_failure(self):
        self.slow=True; core=Core(':memory:'); self.addCleanup(core.close)
        result=Workflow(SimpleNamespace(core=core)).run(['q','next'],DeadlineProvider(self.adapter,1.0))
        self.assertEqual(result['status'],'failed'); self.assertEqual(core.search(''),[]); self.assertEqual(self.calls,1)
    def test_invalid_deadline(self):
        for x in [0,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError): DeadlineProvider(self.adapter,x)
