"""Atomic experimental research storage; no V5 admission."""
import hashlib, hmac, json, sqlite3
from contextlib import closing
from linguistic33 import solve

def run(db, question, key):
    if type(key) is not bytes or len(key) < 32:
        raise ValueError('key limit')
    if type(question) is not str or not 0 < len(question) <= 4096:
        raise ValueError('question limit')
    obj = {'question':question,'result':solve(question),'engine':'linguistic33','evidence_status':'unverified','confidence':None}
    payload = json.dumps(obj,sort_keys=True,allow_nan=False)
    rid = hashlib.sha256(payload.encode()).hexdigest()
    tag = hmac.new(key,b'LOGOS31-experimental\0'+payload.encode(),hashlib.sha256).hexdigest()
    with closing(sqlite3.connect(db)) as c, c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('CREATE TABLE IF NOT EXISTS experimental_reasoning (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS experimental_seals (id TEXT PRIMARY KEY, tag TEXT NOT NULL)')
        old = c.execute('SELECT payload FROM experimental_reasoning WHERE id=?',(rid,)).fetchone()
        seal = c.execute('SELECT tag FROM experimental_seals WHERE id=?',(rid,)).fetchone()
        if old is None and seal is None:
            c.execute('INSERT INTO experimental_reasoning VALUES (?,?)',(rid,payload))
            c.execute('INSERT INTO experimental_seals VALUES (?,?)',(rid,tag))
        elif old != (payload,) or seal is None or not hmac.compare_digest(seal[0],tag):
            raise ValueError('existing record authentication failed')
    return {'id':rid,'authenticated':True,**obj}
