import sqlite3, hmac, hashlib, json, uuid
from contextlib import closing
class IntegrityError(ValueError): pass
class Memory:
    def __init__(self,path,key):
        if type(key) is not bytes or len(key)<32: raise ValueError('32-byte key required')
        self.path,self.key=path,key
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS memory(id TEXT PRIMARY KEY, payload TEXT NOT NULL, mac TEXT NOT NULL)')
    def _mac(self,p): return hmac.new(self.key,p.encode(),hashlib.sha256).hexdigest()
    def _read(self,db,id):
        row=db.execute('SELECT payload,mac FROM memory WHERE id=?',(id,)).fetchone()
        if row is None: raise KeyError(id)
        p,m=row
        if not hmac.compare_digest(self._mac(p),m): raise IntegrityError('invalid MAC')
        r=json.loads(p)
        if r['id']!=id: raise IntegrityError('identity mismatch')
        return r
    def append(self,claim,source,dependencies=(),contradicts=()):
        if any(type(x) is not str or not x.strip() for x in (claim,source)): raise ValueError('claim and source required')
        deps,conf=list(dependencies),list(contradicts)
        if any(type(x) is not str for x in deps+conf): raise ValueError('invalid reference')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            for ref in deps+conf: self._read(db,ref)
            r=dict(id=str(uuid.uuid4()),claim=claim,source=source,dependencies=deps,contradicts=conf,status='unverified')
            p=json.dumps(r,sort_keys=True,separators=(',',':'))
            db.execute('INSERT INTO memory VALUES (?,?,?)',(r['id'],p,self._mac(p)))
            return r
    def get(self,id):
        with closing(sqlite3.connect(self.path)) as db: return self._read(db,id)
