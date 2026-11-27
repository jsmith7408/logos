"""Selective correction of locally adjudicated arithmetic; never promotes evidence."""
import json, uuid
from adjudication import Adjudicator

class Correction:
    def __init__(self, collective):
        self.adjudicator=Adjudicator(collective)
        self.db=collective.db
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS corrections(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def run(self, source):
        evidence=self.adjudicator.prepare(source)
        decisions=[]
        for finding in evidence['findings']:
            status=finding['status']; original=finding['original']
            action={'correct':'preserve','incorrect':'correct'}.get(status,'abstain')
            decisions.append(dict(record=finding['record'], original=original, action=action,
                revised=evidence['conclusion'] if action=='correct' else original))
        report=dict(id=str(uuid.uuid4()), source=source, evidence=evidence['id'], decisions=decisions,
                    authenticated=False, classification='local_arithmetic_correction')
        with self.db:
            self.adjudicator.insert(evidence)
            self.db.execute('INSERT INTO corrections VALUES (?,?)',(report['id'],json.dumps(report)))
        return report
    def get(self, rid):
        row=self.db.execute('SELECT report FROM corrections WHERE id=?',(rid,)).fetchone()
        if row is None: raise KeyError(rid)
        return json.loads(row[0])
