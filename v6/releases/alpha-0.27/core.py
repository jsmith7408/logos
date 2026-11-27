import sqlite3, json, uuid
from typing import Protocol
class Provider(Protocol):
    def reason(self, question: str) -> str: ...
class DemoProvider:
    def reason(self, question): return 'Demonstration only: '+question
class Core:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS research(id TEXT PRIMARY KEY, question TEXT NOT NULL, result TEXT NOT NULL, provenance TEXT NOT NULL)')
    def prepare(self,question,provider):
        if not isinstance(question,str) or not question.strip(): raise ValueError('Question required')
        result=provider.reason(question)
        if not isinstance(result,str): raise ValueError('Invalid provider response')
        record={'id':str(uuid.uuid4()),'question':question,'result':result,'provenance':'demo' if isinstance(provider,DemoProvider) else 'unverified_provider'}
        return record
    def insert(self,record):
        self.db.execute('INSERT INTO research VALUES (:id,:question,:result,:provenance)',record)
    def investigate(self,question,provider):
        record=self.prepare(question,provider)
        with self.db: self.insert(record)
        return record
    def search(self,term):
        return [dict(zip(('id','question','result','provenance'),r)) for r in self.db.execute('SELECT * FROM research WHERE instr(question,?)>0 OR instr(result,?)>0',(term,term))]
    def close(self): self.db.close()
