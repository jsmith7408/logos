import sqlite3
from secure import compare_signed, canonical
from gate import digest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

class TrustGate:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=10,isolation_level=None)
        self.db.executescript('CREATE TABLE IF NOT EXISTS keys(id TEXT PRIMARY KEY, pub BLOB NOT NULL, revoked INTEGER NOT NULL DEFAULT 0); CREATE TABLE IF NOT EXISTS consumed(study TEXT, evidence TEXT, PRIMARY KEY(study,evidence));')
        self.db.execute('CREATE TABLE IF NOT EXISTS semantic(study TEXT, slot TEXT, PRIMARY KEY(study,slot))')
    def enroll(self,id,pub):
        if not isinstance(id,str) or not id: raise ValueError('invalid identity')
        Ed25519PublicKey.from_public_bytes(pub)
        self.db.execute('INSERT INTO keys(id,pub) VALUES(?,?)',(id,pub))
    def revoke(self,id):
        self.db.execute('UPDATE keys SET revoked=1 WHERE id=?',(id,))
    def compare(self,key,b,c,bm,cm,bs,cs,study):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            registry={i:Ed25519PublicKey.from_public_bytes(p) for i,p in self.db.execute('SELECT id,pub FROM keys WHERE revoked=0')}
            result=compare_signed(key,b,c,bm,cm,bs,cs,registry,study)
            if result['status']!='candidate_comparison':
                self.db.rollback(); return result
            if self.db.execute('SELECT COUNT(*) FROM consumed').fetchone()[0] != 2*self.db.execute('SELECT COUNT(*) FROM semantic').fetchone()[0]:
                self.db.rollback(); return {'status':'blocked','reason':'legacy ledger requires migration'}
            slot=digest(canonical([bm[k] for k in ('model','version','settings_digest','questions_digest','baseline_digest')]))
            self.db.execute('INSERT INTO semantic VALUES(?,?)',(study,slot))
            ids=[digest(canonical(m)) for m in (bm,cm)]
            for i in ids:
                self.db.execute('INSERT INTO consumed VALUES(?,?)',(study,i))
            self.db.commit(); return result
        except sqlite3.IntegrityError:
            self.db.rollback(); return {'status':'blocked','reason':'replayed evidence'}
        except BaseException:
            self.db.rollback(); raise
    def close(self): self.db.close()
