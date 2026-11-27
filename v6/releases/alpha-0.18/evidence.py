"""Untrusted evidence snapshots with retrospective integrity/duplication checks.

SHA-256 checks detect unsynchronized edits, not a database-writer adversary.
Source identity and independence are NOT authenticated by this module.
"""
import hashlib, json, uuid
from dependency import dependency_groups
from claims import Claims


class Evidence:
    def __init__(self, collective):
        self.db = collective.db
        Claims(collective)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, report TEXT NOT NULL)')

    def add(self, report_id, index, source, excerpt, stance):
        if type(index) is not int or index < 0 or stance not in ('supports', 'opposes', 'unclear'):
            raise ValueError('invalid relationship')
        for value, limit in ((source, 1000), (excerpt, 8000)):
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError('invalid evidence text')
        row = self.db.execute('SELECT report FROM claims WHERE id=?', (report_id,)).fetchone()
        if not row:
            raise ValueError('unknown claim report')
        claims = json.loads(row[0])['claims']
        if index >= len(claims):
            raise ValueError('unknown claim')
        snapshot = dict(claim_report=report_id, index=index, claim=claims[index],
                        source=source, excerpt=excerpt, stance=stance)
        # Keep Alpha 0.15's original fingerprint representation for compatibility.
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        report = dict(id=str(uuid.uuid4()), snapshot=snapshot, sha256=digest,
                      classification='user_supplied_unverified', authenticated=False, conclusion=None)
        with self.db:
            self.db.execute('INSERT INTO evidence VALUES (?,?)', (report['id'], json.dumps(report)))
        return report

    def _rows(self, report_id, index, limit):
        return self.db.execute("SELECT report FROM evidence WHERE json_extract(report,'$.snapshot.claim_report')=? "
                               "AND json_extract(report,'$.snapshot.index')=? ORDER BY rowid DESC LIMIT ?",
                               (report_id, index, limit)).fetchall()

    def compare(self, report_id, index):
        rows = self._rows(report_id, index, 101)
        records = [json.loads(r[0]) for r in rows[:100]]
        stances = {r['snapshot']['stance'] for r in records}
        return dict(records=records, truncated=len(rows) > 100,
                    reported_conflict={'supports', 'opposes'} <= stances,
                    authenticated=False, conclusion=None)

    def inspect(self, report_id, index, limit=100):
        """Inspect bounded evidence, accounting for duplicates and stale claim snapshots.

        The source labels are attacker/user supplied; the answer never asserts
        that a verified hash implies an authentic or independent source.
        """
        if not isinstance(report_id, str) or not report_id.strip() or len(report_id) > 100 or type(index) is not int or index < 0:
            raise ValueError('invalid evidence query')
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('invalid inspection limit')
        claim_row = self.db.execute('SELECT report FROM claims WHERE id=?', (report_id,)).fetchone()
        if not claim_row:
            raise ValueError('unknown claim report')
        claims = json.loads(claim_row[0]).get('claims', [])
        if index >= len(claims):
            raise ValueError('unknown claim')
        rows = self._rows(report_id, index, limit + 1)
        records = []
        seen = set()
        for (raw,) in rows[:limit]:
            try:
                report = json.loads(raw)
                if not isinstance(report, dict) or not isinstance(report.get('snapshot'), dict):
                    raise ValueError('corrupted evidence record')
                snapshot = report['snapshot']
            except (TypeError, ValueError) as exc:
                raise ValueError('corrupted evidence record') from exc
            # Preserve the Alpha 0.15 legacy canonical JSON for old records.
            expected = hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
            digest_ok = report.get('sha256') == expected
            claim_ok = snapshot.get('claim') == claims[index]
            duplicate_key = (snapshot.get('source'), snapshot.get('excerpt'), snapshot.get('stance'))
            duplicate = duplicate_key in seen
            seen.add(duplicate_key)
            records.append(dict(id=report.get('id'), sha256=report.get('sha256'),
                                fingerprint_matches=digest_ok, claim_snapshot_matches=claim_ok,
                                duplicate_in_window=duplicate, stance=snapshot.get('stance'),
                                source=snapshot.get('source'), excerpt=snapshot.get('excerpt')))
        return dict(report_id=report_id, claim_index=index, records=records,
                    dependency_analysis=dependency_groups(records),
                    truncated=len(rows) > limit, integrity_failures=sum(not r['fingerprint_matches'] for r in records),
                    stale_claim_snapshots=sum(not r['claim_snapshot_matches'] for r in records),
                    repeated_snapshots=sum(r['duplicate_in_window'] for r in records),
                    reported_conflict={'supports', 'opposes'} <= {r['stance'] for r in records if r['fingerprint_matches'] and r['claim_snapshot_matches']},
                    classification='unverified_user_supplied', authenticated=False, conclusion=None,
                    disclaimer='Checks detect accidental or incomplete edits, not authenticated authorship or independent corroboration.')
