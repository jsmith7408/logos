import uuid
from unified import Unified
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
class BoundUnified(Unified):
    def __init__(self,path,admin):
        super().__init__(path,admin)
        db=self._gate.db
        try:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS deployment(id TEXT PRIMARY KEY, authority BLOB NOT NULL)')
            rows=db.execute('SELECT id,authority FROM deployment').fetchall()
            pub=admin.public_bytes(Encoding.Raw,PublicFormat.Raw)
            if not rows:
                if any(db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('keys','studies','admin_ops','consumed','semantic')): raise ValueError('migration required')
                self.deployment=str(uuid.uuid4()); db.execute('INSERT INTO deployment VALUES(?,?)',(self.deployment,pub))
            elif len(rows)==1 and rows[0][1]==pub: self.deployment=rows[0][0]
            else: raise ValueError('authority mismatch')
            db.commit()
        except BaseException:
            db.rollback(); self.close(); raise
    def administer(self,op,sig):
        if op.get('deployment')!=self.deployment: raise ValueError('deployment mismatch')
        return super().administer(op,sig)
