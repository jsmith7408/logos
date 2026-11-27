"""Bounded propositional inference. Stored assertions are not authenticated evidence."""
import json
import re


def atom(value):
    if not isinstance(value, str) or not re.fullmatch(r'!?[A-Za-z][A-Za-z0-9_]{0,63}', value):
        raise ValueError('invalid literal')
    return value


def opposite(value):
    return value[1:] if value.startswith('!') else '!'+value


class Knowledge:
    def __init__(self, db):
        self.db = db
        self.before_infer = None
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS native_facts(literal TEXT, source TEXT, PRIMARY KEY(literal,source))')
            db.execute('CREATE TABLE IF NOT EXISTS native_rules(premises TEXT, conclusion TEXT, PRIMARY KEY(premises,conclusion))')

    def fact(self, literal, source):
        atom(literal)
        if not isinstance(source,str) or not source.strip() or len(source)>1000:
            raise ValueError('source required')
        if source.lower().startswith('attested:'):
            raise ValueError('reserved evidence source')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO native_facts VALUES (?,?)',(literal,source))

    def rule(self, premises, conclusion):
        if not isinstance(premises,(list,tuple)) or not 1<=len(premises)<=16:
            raise ValueError('invalid premises')
        p=json.dumps(sorted(set(map(atom,premises))))
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO native_rules VALUES (?,?)',(p,atom(conclusion)))

    def infer(self, query, budget=10000, *, isolate=False):
        atom(query)
        if type(budget) is not int or not 1<=budget<=10000:
            raise ValueError('invalid budget')
        if self.before_infer is not None: self.before_infer()
        fact_sql = 'SELECT literal,source FROM native_facts'
        if self.before_infer is None: fact_sql += " WHERE source NOT LIKE 'attested:%'"
        facts=self.db.execute(fact_sql+' ORDER BY literal,source LIMIT ?', (budget+1,)).fetchall()
        rules=self.db.execute('SELECT premises,conclusion FROM native_rules ORDER BY premises,conclusion LIMIT ?', (budget+1,)).fetchall()
        proof={}; steps=0
        def result(status):
            return dict(status=status,query=query,proof=proof,steps=steps,authenticated=False)
        if len(facts)+len(rules)>budget:
            return result('budget_exhausted')
        if isolate:
            # Backward dependency cone includes both polarities of every premise.
            relevant={query,opposite(query)}
            while True:
                before=len(relevant)
                for raw,conclusion in rules:
                    if steps>=budget:
                        return result('budget_exhausted')
                    steps+=1
                    if conclusion in relevant:
                        for p in json.loads(raw):
                            relevant.update((p,opposite(p)))
                if len(relevant)==before:
                    break
            facts=[(l,s) for l,s in facts if l in relevant]
            rules=[(p,c) for p,c in rules if c in relevant]
        for literal,source in facts:
            proof.setdefault(literal,{'sources':[]})['sources'].append(source)
        steps+=len(facts)
        if steps>budget:
            return result('budget_exhausted')
        while True:
            # Conservative global conflict gate, including derived contradictions.
            if any(opposite(x) in proof for x in proof):
                return result('conflict')
            changed=False
            for raw,conclusion in rules:
                if steps>=budget:
                    return result('budget_exhausted')
                steps+=1
                premises=json.loads(raw)
                if conclusion not in proof and all(p in proof for p in premises):
                    proof[conclusion]={'premises':premises}; changed=True
            if not changed:
                return result('supported' if query in proof else 'refuted' if opposite(query) in proof else 'unknown')
