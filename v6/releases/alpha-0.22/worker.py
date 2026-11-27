"""Bounded local Ollama client subprocess; no arbitrary provider deserialization."""
import json, subprocess, sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from providers import OllamaProvider, ProviderError

class DeadlineProvider:
    def __init__(self, provider, deadline=35):
        if type(provider) is not OllamaProvider: raise TypeError('OllamaProvider required')
        if type(deadline) not in (int,float) or not math.isfinite(deadline) or not 0<deadline<=150: raise ValueError('invalid deadline')
        self.provider, self.deadline = provider, deadline
    def reason(self, question):
        if not isinstance(question,str) or not question.strip() or len(question)>4000: raise ValueError('invalid question')
        payload=json.dumps({'config':vars(self.provider),'question':question})
        try:
            result=subprocess.run([sys.executable,'-I',str(Path(__file__).resolve()),'--child'],input=payload,capture_output=True,text=True,timeout=self.deadline,check=False)
        except subprocess.TimeoutExpired as exc:
            raise ProviderError('worker deadline exceeded') from exc
        if result.returncode: raise ProviderError('worker failed')
        try: value=json.loads(result.stdout)
        except ValueError as exc: raise ProviderError('invalid worker output') from exc
        if not isinstance(value,str) or not value.strip(): raise ProviderError('invalid worker response')
        return value

if __name__=='__main__' and sys.argv[1:]==['--child']:
    # Isolated mode excludes the script directory; explicitly restore trusted local source.
    data=json.load(sys.stdin)
    print(json.dumps(OllamaProvider(**data['config']).reason(data['question'])))
