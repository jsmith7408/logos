#!/usr/bin/env python3
"""
Neuro-Symbolic Kernel (LOGOS-compatible style)

Combines:
- Symbolic propositional inference (facts + rules + bounded forward chaining + conflict detection)
- Optional neural/provider proposal path
- Strategy routing that prefers symbolic results
- Simple reflective monitoring hooks

All assertions remain unauthenticated by design.
"""

import json
import re
import sqlite3
import time
import uuid
from typing import Optional, Callable, Dict, Any, List


# ---------------------------------------------------------------------------
# Symbolic core
# ---------------------------------------------------------------------------

def atom(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'!?[A-Za-z][A-Za-z0-9_]{0,63}', value):
        raise ValueError('invalid literal')
    return value


def opposite(value: str) -> str:
    return value[1:] if value.startswith('!') else '!' + value


class SymbolicKnowledge:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS ns_facts(literal TEXT, source TEXT, PRIMARY KEY(literal,source))')
            db.execute('CREATE TABLE IF NOT EXISTS ns_rules(premises TEXT, conclusion TEXT, PRIMARY KEY(premises,conclusion))')

    def fact(self, literal: str, source: str) -> None:
        atom(literal)
        if not isinstance(source, str) or not source.strip() or len(source) > 1000:
            raise ValueError('source required')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO ns_facts VALUES (?,?)', (literal, source))

    def rule(self, premises: List[str], conclusion: str) -> None:
        if not isinstance(premises, (list, tuple)) or not 1 <= len(premises) <= 16:
            raise ValueError('invalid premises')
        p = json.dumps(sorted(set(map(atom, premises))))
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO ns_rules VALUES (?,?)', (p, atom(conclusion)))

    def infer(self, query: str, budget: int = 10000, isolate: bool = False) -> Dict[str, Any]:
        atom(query)
        if not isinstance(budget, int) or not 1 <= budget <= 10000:
            raise ValueError('invalid budget')

        facts = self.db.execute(
            'SELECT literal,source FROM ns_facts ORDER BY literal,source LIMIT ?', (budget + 1,)
        ).fetchall()
        rules = self.db.execute(
            'SELECT premises,conclusion FROM ns_rules ORDER BY premises,conclusion LIMIT ?', (budget + 1,)
        ).fetchall()

        proof: Dict[str, Any] = {}
        steps = 0

        def result(status: str) -> Dict[str, Any]:
            return {
                'status': status,
                'query': query,
                'proof': proof,
                'steps': steps,
                'authenticated': False,
                'source': 'symbolic',
            }

        if len(facts) + len(rules) > budget:
            return result('budget_exhausted')

        if isolate:
            relevant = {query, opposite(query)}
            while True:
                before = len(relevant)
                for raw, conclusion in rules:
                    if steps >= budget:
                        return result('budget_exhausted')
                    steps += 1
                    if conclusion in relevant:
                        for p in json.loads(raw):
                            relevant.update((p, opposite(p)))
                if len(relevant) == before:
                    break
            facts = [(l, s) for l, s in facts if l in relevant]
            rules = [(p, c) for p, c in rules if c in relevant]

        for literal, source in facts:
            proof.setdefault(literal, {'sources': []})['sources'].append(source)
        steps += len(facts)
        if steps > budget:
            return result('budget_exhausted')

        while True:
            if any(opposite(x) in proof for x in proof):
                return result('conflict')
            changed = False
            for raw, conclusion in rules:
                if steps >= budget:
                    return result('budget_exhausted')
                steps += 1
                premises = json.loads(raw)
                if conclusion not in proof and all(p in proof for p in premises):
                    proof[conclusion] = {'premises': premises}
                    changed = True
            if not changed:
                if query in proof:
                    return result('supported')
                if opposite(query) in proof:
                    return result('refuted')
                return result('unknown')


# ---------------------------------------------------------------------------
# Optional neural / provider interface
# ---------------------------------------------------------------------------

class NeuralProposer:
    """
    Pluggable interface for a neural or local model.
    The default implementation is a no-op that returns nothing.
    Replace `propose` with a call to Ollama, a local LLM, etc.
    """

    def propose(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Should return a dict like:
            {'literals': ['A', '!B'], 'rules': [[['A'], 'C']], 'confidence': 0.7}
        or None if no proposal.
        """
        return None


# ---------------------------------------------------------------------------
# Neuro-symbolic strategy router
# ---------------------------------------------------------------------------

class NeuroSymbolicStrategy:
    def __init__(self, db: sqlite3.Connection, proposer: Optional[NeuralProposer] = None):
        self.db = db
        self.knowledge = SymbolicKnowledge(db)
        self.proposer = proposer or NeuralProposer()
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS ns_reports(id TEXT PRIMARY KEY, report TEXT NOT NULL)')

    def run(self, question: str, prefer_symbolic: bool = True) -> Dict[str, Any]:
        start = time.monotonic()
        report = {
            'id': str(uuid.uuid4()),
            'question': question,
            'authenticated': False,
            'elapsed_seconds': None,
        }

        # 1. Try pure symbolic path if the question looks like a literal
        if question.startswith('infer:') or question.startswith('infer-local:'):
            isolate = question.startswith('infer-local:')
            q = question.split(':', 1)[1].strip()
            evidence = self.knowledge.infer(q, isolate=isolate)
            report.update({
                'strategy': 'symbolic_inference',
                'result': evidence,
                'classification': evidence['status'],
            })
        else:
            # 2. Optional neural proposal
            proposal = self.proposer.propose(question)
            if proposal and prefer_symbolic:
                # Optionally ingest proposed facts/rules (still unauthenticated)
                for lit in proposal.get('literals', []):
                    try:
                        self.knowledge.fact(lit, source='neural_proposal')
                    except ValueError:
                        pass
                for premises, conclusion in proposal.get('rules', []):
                    try:
                        self.knowledge.rule(premises, conclusion)
                    except ValueError:
                        pass
                # Then try to infer something useful
                # (simple heuristic: treat first proposed literal as query)
                if proposal.get('literals'):
                    evidence = self.knowledge.infer(proposal['literals'][0])
                    report.update({
                        'strategy': 'neuro_symbolic_proposal',
                        'proposal': proposal,
                        'result': evidence,
                        'classification': evidence['status'],
                    })
                else:
                    report.update({
                        'strategy': 'neural_proposal_only',
                        'proposal': proposal,
                        'classification': 'proposed',
                    })
            else:
                report.update({
                    'strategy': 'abstention',
                    'classification': 'no_symbolic_or_proposal',
                })

        report['elapsed_seconds'] = time.monotonic() - start
        with self.db:
            self.db.execute(
                'INSERT INTO ns_reports VALUES (?,?)',
                (report['id'], json.dumps(report)),
            )
        return report


# ---------------------------------------------------------------------------
# Minimal reflective monitor
# ---------------------------------------------------------------------------

class ReflectiveMonitor:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        with db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS ns_activity(
                    id TEXT PRIMARY KEY,
                    created REAL,
                    summary TEXT
                )
            ''')

    def record(self, report: Dict[str, Any]) -> None:
        summary = {
            'strategy': report.get('strategy'),
            'classification': report.get('classification'),
            'elapsed': report.get('elapsed_seconds'),
            'authenticated': report.get('authenticated'),
        }
        with self.db:
            self.db.execute(
                'INSERT INTO ns_activity VALUES (?,?,?)',
                (str(uuid.uuid4()), time.time(), json.dumps(summary)),
            )

    def summary(self, limit: int = 20) -> Dict[str, Any]:
        rows = self.db.execute(
            'SELECT summary FROM ns_activity ORDER BY created DESC LIMIT ?', (limit,)
        ).fetchall()
        return {
            'recent': [json.loads(r[0]) for r in rows],
            'count': len(rows),
            'authenticated': False,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    db = sqlite3.connect(':memory:')
    strategy = NeuroSymbolicStrategy(db)
    monitor = ReflectiveMonitor(db)

    # Add some symbolic knowledge
    strategy.knowledge.fact('Bird', 'demo')
    strategy.knowledge.rule(['Bird'], 'CanFly')

    print('=== Symbolic inference ===')
    r1 = strategy.run('infer:CanFly')
    monitor.record(r1)
    print(json.dumps(r1, indent=2))

    print('\n=== Unknown query ===')
    r2 = strategy.run('infer:IsFish')
    monitor.record(r2)
    print(json.dumps(r2, indent=2))

    print('\n=== Reflection summary ===')
    print(json.dumps(monitor.summary(), indent=2))

    db.close()


if __name__ == '__main__':
    demo()
