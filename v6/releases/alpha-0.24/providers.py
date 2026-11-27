"""Loopback-only Ollama adapter. No proxy, redirects, or remote endpoints."""
import http.client, json, time

class ProviderError(RuntimeError): pass
class OllamaProvider:
    def __init__(self, model, port=11434, timeout=30, max_bytes=65536, max_tokens=512):
        if not isinstance(model,str) or not model.strip() or len(model)>200: raise ValueError('invalid model')
        if type(port) is not int or not 1<=port<=65535: raise ValueError('invalid port')
        if type(timeout) not in (int,float) or not 0<timeout<=120: raise ValueError('invalid timeout')
        if type(max_bytes) is not int or not 128<=max_bytes<=1048576: raise ValueError('invalid byte limit')
        if type(max_tokens) is not int or not 1<=max_tokens<=4096: raise ValueError('invalid token budget')
        self.model,self.port,self.timeout,self.max_bytes,self.max_tokens=model,port,timeout,max_bytes,max_tokens
    def reason(self, question):
        if not isinstance(question,str) or not question.strip() or len(question)>4000: raise ValueError('invalid question')
        deadline=time.monotonic()+self.timeout
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=self.timeout)
        try:
            conn.request('POST','/api/generate',json.dumps(dict(model=self.model,prompt=question,stream=False,options={'num_predict':self.max_tokens})),{'Content-Type':'application/json'})
            response=conn.getresponse()
            if response.status!=200: raise ProviderError('HTTP status '+str(response.status))
            data=bytearray()
            while True:
                if time.monotonic()>=deadline: raise ProviderError('deadline exceeded')
                chunk=response.read1(min(4096,self.max_bytes+1-len(data)))
                if not chunk: break
                data.extend(chunk)
                if len(data)>self.max_bytes: raise ProviderError('response too large')
            obj=json.loads(data)
            if not isinstance(obj,dict) or obj.get('done') is not True or not isinstance(obj.get('response'),str) or not obj['response'].strip(): raise ProviderError('invalid or incomplete response')
            return obj['response']
        except (OSError,http.client.HTTPException,ValueError) as exc:
            raise ProviderError('local provider transport or decoding failure') from exc
        finally: conn.close()
