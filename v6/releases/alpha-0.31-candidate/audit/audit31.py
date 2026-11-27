"""Authenticate experimental records without admitting them as V5 evidence."""
import hashlib, hmac, json, sqlite3
from contextlib import closing

def seal(db, record_id, key):
    return _access(db, record_id, key, True)

def retrieve(db, record_id, key):
    return _access(db, record_id, key, False)

def _access(db, record_id, key, write):
    if type(key) is not bytes or len(key) < 32:
        raise ValueError('key must contain at least 32 bytes')
    with closing(sqlite3.connect(db)) as c, c:
        c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        row = c.execute('SELECT payload FROM experimental_reasoning WHERE id=?',(record_id,)).fetchone()
        if row is None: raise ValueError('unknown record')
        payload = row[0]
        if hashlib.sha256(payload.encode()).hexdigest() != record_id:
            raise ValueError('record integrity')
        obj = json.loads(payload)
        if obj.get('evidence_status') != 'unverified': raise ValueError('evidence boundary')
        tag = hmac.new(key, b'LOGOS31-experimental\0'+payload.encode(), hashlib.sha256).hexdigest()
        if write:
            c.execute('CREATE TABLE IF NOT EXISTS experimental_seals (id TEXT PRIMARY KEY, tag TEXT NOT NULL)')
            c.execute('INSERT OR IGNORE INTO experimental_seals VALUES (?,?)',(record_id,tag))
        row = c.execute('SELECT tag FROM experimental_seals WHERE id=?',(record_id,)).fetchone()
        if row is None or not hmac.compare_digest(row[0],tag): raise ValueError('authentication failed')
        return {'id':record_id,'authenticated':True,**obj}
