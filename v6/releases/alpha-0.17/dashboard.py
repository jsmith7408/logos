"""Local single-user dashboard. No external assets or remote endpoints."""
import argparse, html, secrets, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from core import Core, DemoProvider
from bridge import Application
from workflow import Workflow
from providers import OllamaProvider
from worker import DeadlineProvider
from collective import Collective
from correction import Correction
from adjudication import evaluate
from strategy import Strategy
from claims import Claims
from evidence import Evidence

def serve(path, port=8765):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def allowed(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'
        def send(self, status, body):
            self.send_response(status); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'"); self.end_headers(); self.wfile.write(body.encode())
        def do_GET(self):
            if not self.allowed(): return self.send(403,'Forbidden')
            if self.path!='/': return self.send(404,'Not found')
            c=Core(path)
            try:
                w=Workflow(Application(c,None))
                records=c.db.execute('SELECT question,result,provenance FROM research ORDER BY rowid DESC LIMIT 50').fetchall()
                runs=c.db.execute('SELECT id,status FROM runs ORDER BY rowid DESC LIMIT 50').fetchall()
                esc=lambda x:html.escape(str(x))
                body='<!doctype html><meta charset=utf-8><title>LOGOS V6</title><style>body{font:16px system-ui;max-width:900px;margin:40px auto;padding:16px;background:#111827;color:#eee}input,textarea,select,button{font:inherit;margin:8px;padding:8px}textarea{width:90%}pre{white-space:pre-wrap}article{border:1px solid #64748b;padding:16px;margin:12px 0}</style><h1>LOGOS V6 · Research dashboard</h1><p>Local research only. Independent validation and security assessment outstanding. V5 owner-authorized release; evidence submissions are not exposed here.</p>'
                body+=f'<form method=post action=/run><input type=hidden name=token value="{token}"><label>Questions (one per line, up to five)</label><textarea name=questions required maxlength=20000></textarea><label>Provider <select name=provider><option value=demo>Demonstration</option><option value=ollama>Local Ollama</option></select></label><label>Installed model <input name=model maxlength=200></label><button>Run research</button></form><h2>Execution history</h2>'
                for rid,status in runs: body+=f'<article>{esc(rid)} — {esc(status)}<pre>{esc(w.status(rid))}</pre></article>'
                collective=Collective(Application(c,None)); Correction(collective)
                body+=f'<h2>Collective arithmetic</h2><form method=post action=/collective><input type=hidden name=token value="{token}"><label>Integer arithmetic expression <input name=questions required maxlength=256></label><label>Provider <select name=provider><option value=demo>Demonstration</option><option value=ollama>Local Ollama</option></select></label><label>Model A <input name=model maxlength=200></label><label>Model B <input name=model_b maxlength=200></label><button>Compare and verify</button></form>'
                Strategy(Application(c,None))
                body+=f'<h2>Adaptive research</h2><form method=post action=/adaptive><input type=hidden name=token value="{token}"><label>Question or arithmetic expression <input name=questions required maxlength=4000></label><label>Provider <select name=provider><option value=demo>Demonstration</option><option value=ollama>Local Ollama</option></select></label><label>Model A <input name=model maxlength=200></label><label>Model B <input name=model_b maxlength=200></label><button>Choose strategy and run</button></form>'
                Claims(collective)
                body+=f'<h2>Structured claim comparison</h2><form method=post action=/claims><input type=hidden name=token value="{token}"><label>Collective investigation ID <input name=source required maxlength=36></label><button>Compare structured claims</button></form><p>Requires provider JSON claim arrays; no truth verification.</p>'
                Evidence(collective)
                body+=f'<h2>Evidence inspection</h2><form method=post action=/evidence-inspect><input type=hidden name=token value="{token}"><label>Claim report ID <input name=source required maxlength=36></label><label>Claim index <input name=index type=number min=0 required></label><button>Inspect reported evidence, duplicates and hashes</button></form>'
                body+=f'<h2>Evidence snapshots</h2><form method=post action=/evidence><input type=hidden name=token value="{token}"><label>Claim report ID <input name=source required maxlength=36></label><label>Claim index (zero-based) <input name=index type=number min=0 required></label><label>Source label <input name=label required maxlength=1000></label><label>Excerpt <textarea name=excerpt required maxlength=8000></textarea></label><select name=stance><option>supports</option><option>opposes</option><option>unclear</option></select><button>Record unverified evidence</button></form>'
                for table in ('collective','adjudication','corrections','strategies','claims','evidence'):
                    body+=f'<h3>{table}</h3>'
                    for (report,) in c.db.execute(f'SELECT report FROM {table} ORDER BY rowid DESC LIMIT 20'):
                        body+=f'<article><pre>{esc(report)}</pre></article>'
                body+='<h2>Research records</h2>' 
                for q,r,p in records: body+=f'<article><strong>{esc(q)}</strong><p>{esc(p)}</p><pre>{esc(r)}</pre></article>'
                self.send(200,body)
            finally: c.close()
        def do_POST(self):
            if not self.allowed() or self.path not in ('/run','/collective','/adaptive','/claims','/evidence','/evidence-inspect'): return self.send(403,'Forbidden')
            if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}'): return self.send(403,'Forbidden')
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=100000: raise ValueError()
                form=urllib.parse.parse_qs(self.rfile.read(n).decode(),max_num_fields=8)
                if not secrets.compare_digest(form.get('token',[''])[0],token): return self.send(403,'Forbidden')
                if self.path=='/evidence-inspect':
                    c=Core(path)
                    try: result=Evidence(Collective(Application(c,None))).inspect(form['source'][0],int(form['index'][0]))
                    finally: c.close()
                    # Escape the entire report, including user-provided source labels and excerpts.
                    import json
                    return self.send(200,'<!doctype html><meta charset=utf-8><title>LOGOS Evidence Inspection</title><h1>Evidence integrity inspection</h1><p>Unverified user-supplied sources. Hash matching does not prove authenticity.</p><pre>'+html.escape(json.dumps(result,indent=2))+'</pre><a href="/">Dashboard</a>')
                if self.path=='/evidence':
                    c=Core(path)
                    try: Evidence(Collective(Application(c,None))).add(form['source'][0],int(form['index'][0]),form['label'][0],form['excerpt'][0],form['stance'][0])
                    finally: c.close()
                    self.send_response(303); self.send_header('Location','/'); self.end_headers(); return
                if self.path=='/claims':
                    c=Core(path)
                    try: Claims(Collective(Application(c,None))).run(form['source'][0])
                    finally: c.close()
                    self.send_response(303); self.send_header('Location','/'); self.end_headers(); return
                qs=form['questions'][0].splitlines(); kind=form['provider'][0]
                if kind=='demo': provider=DemoProvider()
                elif kind=='ollama': provider=DeadlineProvider(OllamaProvider(form['model'][0]),35)
                else: raise ValueError()
                c=Core(path)
                try:
                    app=Application(c,None)
                    if self.path=='/run': Workflow(app).run(qs,provider,max_steps=5)
                    elif self.path=='/adaptive':
                        other=DemoProvider() if kind=='demo' else DeadlineProvider(OllamaProvider(form['model_b'][0]),35)
                        Strategy(app).run(form['questions'][0],{'A':provider,'B':other},budget=70)
                    else:
                        expression=form['questions'][0]; evaluate(expression)
                        other=DemoProvider() if kind=='demo' else DeadlineProvider(OllamaProvider(form['model_b'][0]),35)
                        collective=Collective(app); correction=Correction(collective)
                        report=collective.run(expression,{'A':provider,'B':other},budget=70)
                        correction.run(report['id'])
                finally: c.close()
            except (ValueError,KeyError,UnicodeError,SyntaxError,ZeroDivisionError): return self.send(400,'Invalid research request')
            self.send_response(303); self.send_header('Location','/'); self.end_headers()
    return HTTPServer(('127.0.0.1',port),Handler)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--db',default='research.sqlite'); p.add_argument('--port',type=int,default=8765); a=p.parse_args()
    with serve(a.db,a.port) as server:
        print(f'http://127.0.0.1:{server.server_port}',flush=True); server.serve_forever()
