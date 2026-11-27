"""Local experimental reasoning records; never admits evidence or modifies V5."""
import hashlib, json, sqlite3
from linguistic33 import solve

def record(db, question):
    if type(question) is not str or not 0 < len(question) <= 4096:
        raise ValueError('question limit')
    result = solve(question)
    payload = json.dumps({'question':question,'result':result,'engine':'linguistic33','evidence_status':'unverified','confidence':None},sort_keys=True,allow_nan=False)
    key = hashlib.sha256(payload.encode()).hexdigest()
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS experimental_reasoning (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        conn.execute('INSERT OR IGNORE INTO experimental_reasoning VALUES (?,?)',(key,payload))
        stored = conn.execute('SELECT payload FROM experimental_reasoning WHERE id=?',(key,)).fetchone()[0]
        if stored != payload: raise ValueError('record integrity')
    return {'id':key,**json.loads(payload)}
