"""Local V6 bridge to the preserved V5 restricted service."""
import json, subprocess, sys
from pathlib import Path

class GateUnavailable(RuntimeError): pass
class Bridge:
    def __init__(self, path, authority, timeout=10):
        self.path=str(Path(path).resolve()); self.authority=authority; self.timeout=timeout
    def request(self, request):
        raw=json.dumps(request,allow_nan=False)
        if len(raw)>2_000_000: raise ValueError('request too large')
        try:
            p=subprocess.run([sys.executable,str(Path(__file__).resolve().parent/'v5'/'service.py'),self.path,self.authority],input=raw+'\n',capture_output=True,text=True,timeout=self.timeout,check=True)
            result=json.loads(p.stdout)
            if not isinstance(result,dict): raise ValueError('invalid reply')
            return result
        except (OSError,subprocess.SubprocessError,ValueError) as e:
            raise GateUnavailable('V5 service unavailable; no comparison accepted') from e

class Application:
    def __init__(self, core, bridge): self.core=core; self.bridge=bridge
    def investigate(self, question, provider): return self.core.investigate(question,provider)
    def compare(self, request):
        if request.get('action')!='compare': raise ValueError('comparison required')
        return self.bridge.request(request)
