"""Local V6 research and V5 signed-comparison integration."""
import hashlib
import json
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from v6.core import Core


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


class Engine:
    def __init__(self, research_db, gate_db, admin_public_hex, timeout=10):
        if Path(research_db).resolve() == Path(gate_db).resolve():
            raise ValueError('Separate research and gate databases required')
        if len(bytes.fromhex(admin_public_hex)) != 32 or timeout <= 0:
            raise ValueError('Invalid public key or timeout')
        self.core = Core(research_db)
        self.command = [sys.executable, str(ROOT / 'v5/service.py'),
                        str(Path(gate_db).resolve()), admin_public_hex]
        self.timeout = timeout
        self.core.db.execute('CREATE TABLE IF NOT EXISTS comparisons('
                             'id TEXT PRIMARY KEY, research_id TEXT, request TEXT NOT NULL, '
                             'digest TEXT NOT NULL, status TEXT NOT NULL, response TEXT)')
        self.core.db.commit()

    def investigate(self, question, provider):
        return self.core.investigate(question, provider)

    def search(self, term):
        return self.core.search(term)

    def _call(self, request):
        proc = subprocess.run(self.command, input=encode(request)+'\n', text=True,
                              capture_output=True, timeout=self.timeout, check=True)
        result = json.loads(proc.stdout)
        if type(result) is not dict:
            raise ValueError('Invalid gate response')
        return result

    def identity(self):
        return self._call({'action': 'identity'})

    def administer(self, operation, signature):
        return self._call({'action': 'administer', 'operation': operation,
                           'signature': signature.hex()})

    def compare(self, request, research_id=None):
        fields = {'action','study','key','questions','baseline','settings','b','c','bm','cm','bs','cs'}
        if type(request) is not dict or set(request) != fields or request['action'] != 'compare':
            raise ValueError('Invalid comparison request')
        if research_id is not None and not self.core.db.execute(
                'SELECT 1 FROM research WHERE id=?', (research_id,)).fetchone():
            raise ValueError('Unknown research record')
        raw = encode(request)
        ident = str(uuid.uuid4())
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.core.db:
            self.core.db.execute('INSERT INTO comparisons VALUES(?,?,?,?,?,NULL)',
                                 (ident, research_id, raw, digest, 'pending'))
        try:
            result = self._call(json.loads(raw))
            status = result.get('status')
            if status not in ('blocked', 'candidate_comparison'):
                raise ValueError('Unexpected gate status')
            if status == 'candidate_comparison' and type(result.get('metrics')) is not dict:
                raise ValueError('Missing comparison metrics')
            response = encode(result)
        except (subprocess.SubprocessError, OSError, ValueError):
            # The gate might have consumed evidence before a timeout or lost reply.
            status = 'indeterminate'
            response = encode({'status': status, 'reason': 'gate outcome unavailable'})
        with self.core.db:
            self.core.db.execute('UPDATE comparisons SET status=?,response=? WHERE id=?',
                                 (status, response, ident))
        return self.get_comparison(ident)

    def get_comparison(self, ident):
        row = self.core.db.execute('SELECT id,research_id,digest,status,response FROM comparisons WHERE id=?',
                                   (ident,)).fetchone()
        if row is None:
            raise KeyError(ident)
        return dict(id=row[0], research_id=row[1], digest=row[2], status=row[3],
                    response=json.loads(row[4]) if row[4] is not None else None)

    def close(self):
        self.core.close()
