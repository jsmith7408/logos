"""Capture independent calls and compare text without claiming factual validation."""
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from v62.providers import Provider, ProviderError, canonical, transport


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Collector:
    def __init__(self, database):
        self.db = sqlite3.connect(database)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS model_runs(
                id TEXT PRIMARY KEY, prompt TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS model_calls(
                id TEXT PRIMARY KEY, run_id TEXT NOT NULL, provider TEXT NOT NULL,
                model TEXT NOT NULL, url TEXT NOT NULL, payload TEXT NOT NULL,
                request_hash TEXT NOT NULL, started TEXT NOT NULL, finished TEXT,
                status TEXT NOT NULL, raw BLOB, raw_hash TEXT, answer TEXT,
                reported_model TEXT, error TEXT, FOREIGN KEY(run_id) REFERENCES model_runs(id));
        """)
        self.db.execute('PRAGMA foreign_keys=ON')

    def run(self, prompt, providers, *, allow_network=False, send=transport):
        providers = tuple(providers)
        if not 1 <= len(providers) <= 4 or any(type(p) is not Provider for p in providers):
            raise ValueError('Select one to four providers')
        if len({(p.name, p.model) for p in providers}) != len(providers):
            raise ValueError('Duplicate provider/model pair')
        prepared = [(p, *p.prepare(prompt)) for p in providers]
        if not allow_network:
            raise PermissionError('Explicit network opt-in required')
        run_id = str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO model_runs VALUES(?,?,?)', (run_id, prompt, now()))
        for p, url, payload in prepared:
            ident = str(uuid.uuid4())
            body = canonical(payload)
            request_hash = sha(canonical([url, payload]).encode())
            with self.db:
                self.db.execute(
                    'INSERT INTO model_calls(id,run_id,provider,model,url,payload,request_hash,started,status)'
                    ' VALUES(?,?,?,?,?,?,?,?,?)',
                    (ident, run_id, p.name, p.model, url, body, request_hash, now(), 'pending'))
            raw = None
            answer = None
            reported = None
            error = None
            try:
                raw = send(url, payload, p.headers(), p.timeout)
                if not isinstance(raw, bytes):
                    raw = None
                    raise ProviderError('invalid_transport')
                if len(raw) > 2 * 1024 * 1024:
                    raw = None
                    raise ProviderError('response_too_large')
                parsed = p.parse(raw)
                answer, reported = parsed['answer'], parsed['reported_model']
                status = 'captured_unverified'
            except ProviderError as exc:
                status = 'failed'
                # Only allow known categories; never persist arbitrary exceptions or secrets.
                known = {'network_error','response_too_large','invalid_response',
                         'incomplete_response','empty_answer','invalid_transport',
                         'missing_or_invalid_credential'}
                code = str(exc)
                error = code if code in known or (code.startswith('http_') and
                        len(code) == 8 and code[5:].isdigit()) else 'provider_error'
            except Exception:
                status, error = 'failed', 'unexpected_error'
            with self.db:
                self.db.execute(
                    'UPDATE model_calls SET finished=?,status=?,raw=?,raw_hash=?,answer=?,'
                    'reported_model=?,error=? WHERE id=?',
                    (now(), status, raw, sha(raw) if raw is not None else None,
                     answer, reported, error, ident))
        return self.report(run_id)

    def report(self, run_id):
        if not self.db.execute('SELECT 1 FROM model_runs WHERE id=?', (run_id,)).fetchone():
            raise KeyError(run_id)
        cols = ('provider','model','reported_model','status','answer','raw_hash','error')
        rows = [dict(zip(cols, row)) for row in self.db.execute(
            'SELECT provider,model,reported_model,status,answer,raw_hash,error FROM model_calls '
            'WHERE run_id=? ORDER BY rowid', (run_id,))]
        answers = [r['answer'] for r in rows if r['status'] == 'captured_unverified']
        if len(answers) < 2:
            comparison = 'insufficient_responses'
        elif len(answers) != len(rows):
            comparison = 'partial_coverage'
        elif all(a == answers[0] for a in answers):
            comparison = 'exact_text_agreement'
        else:
            comparison = 'text_differs'
        return {'run_id': run_id, 'comparison': comparison,
                'evidence_status': 'unverified', 'calls': rows}

    def close(self):
        self.db.close()
