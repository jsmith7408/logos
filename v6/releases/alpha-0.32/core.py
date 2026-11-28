import sqlite3, uuid
from typing import Protocol
class Provider(Protocol):
    def reason(self, question: str) -> str: ...
class DemoProvider:
    def reason(self, question): return 'Demonstration only: '+question
class AuthorizationError(RuntimeError): pass
# Capture trusted implementation; never dispatch through caller-controlled instances.
_demo_reason = DemoProvider.reason
class Core:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        try:
            self.db.execute('CREATE TABLE IF NOT EXISTS research(id TEXT PRIMARY KEY, question TEXT NOT NULL, result TEXT NOT NULL, provenance TEXT NOT NULL)')
        except BaseException:
            self.db.close(); raise
        self._closed=False
    def prepare(self,question,provider):
        if type(question) is not str or not question.strip(): raise ValueError('Question required')
        if type(provider) is not DemoProvider or vars(provider) or DemoProvider.reason is not _demo_reason:
            raise AuthorizationError('Provider not authorized')
        result=_demo_reason(provider,question)
        return {'id':str(uuid.uuid4()),'question':question,'result':result,'provenance':'demo'}
    def insert(self,record):
        if type(record) is not dict or set(record)!= {'id','question','result','provenance'} or any(type(v) is not str for v in record.values()) or record['provenance']!='demo' or record['result']!='Demonstration only: '+record['question'] or not record['question'].strip():
            raise AuthorizationError('Invalid demonstration record')
        self.db.execute('INSERT INTO research VALUES (:id,:question,:result,:provenance)',record)
    def investigate(self,question,provider):
        record=self.prepare(question,provider)
        with self.db: self.insert(record)
        return record
    def search(self,term):
        return [dict(zip(('id','question','result','provenance'),r)) for r in self.db.execute('SELECT * FROM research WHERE instr(question,?)>0 OR instr(result,?)>0',(term,term))]
    def close(self):
        if not self._closed:
            self.db.close(); self._closed=True
    def __enter__(self):
        if self._closed: raise RuntimeError('Core closed')
        return self
    def __exit__(self,*exc): self.close()
