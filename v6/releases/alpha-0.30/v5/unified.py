from lifecycle import TrustGate
from secure import canonical
from gate import digest
from cryptography.exceptions import InvalidSignature
import json

class Unified:
    def __init__(self,path,admin):
        self._gate=TrustGate(path)
        self._admin=admin
        self._gate.db.executescript('CREATE TABLE IF NOT EXISTS admin_ops(nonce TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS studies(id TEXT PRIMARY KEY, binding TEXT NOT NULL);')
    def administer(self,op,sig):
        self._admin.verify(sig,canonical(op))
        db=self._gate.db
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('INSERT INTO admin_ops VALUES(?)',(op['nonce'],))
            action=op['action']
            if action=='enroll': self._gate.enroll(op['id'],bytes.fromhex(op['pub']))
            elif action=='revoke': self._gate.revoke(op['id'])
            elif action=='study': db.execute('INSERT INTO studies VALUES(?,?)',(op['id'],canonical(op['binding']).decode()))
            else: raise ValueError('unknown action')
            db.commit()
        except BaseException:
            db.rollback(); raise
    def compare(self,study,key,questions,baseline,settings,b,c,bm,cm,bs,cs):
        binding=dict(key_digest=digest(canonical(key)),questions_digest=digest(questions),baseline_digest=digest(baseline),settings_digest=digest(settings))
        row=self._gate.db.execute('SELECT binding FROM studies WHERE id=?',(study,)).fetchone()
        if not row or json.loads(row[0])!=binding or any(m.get(k)!=v for m in (bm,cm) for k,v in binding.items()):
            return {'status':'blocked','reason':'unregistered or mismatched study binding'}
        return self._gate.compare(key,b,c,bm,cm,bs,cs,study)
    def close(self): self._gate.close()
