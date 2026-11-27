"""Retired third-party AI adapter: fail closed, including loopback."""
class ProviderError(RuntimeError): pass
class OllamaProvider:
    def __init__(self, model, port=11434, timeout=30, max_bytes=65536, max_tokens=512):
        # Preserve constructor for historical fixture compatibility only.
        self.model,self.port,self.timeout,self.max_bytes,self.max_tokens=model,port,timeout,max_bytes,max_tokens
    def reason(self, question):
        raise ProviderError('Third-party AI inference disabled by Alpha 0.28 policy')
