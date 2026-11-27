"""Restricted rational arithmetic verifier; never executes provider text."""
import ast, re, json, uuid
from fractions import Fraction

def evaluate(expression):
    if not isinstance(expression,str) or len(expression)>256: raise ValueError('expression limit')
    tree=ast.parse(expression,mode='eval')
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value) is int and abs(n.value)<=10**12: return Fraction(n.value)
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=visit(n.operand); return -v if isinstance(n.op,ast.USub) else v
        if isinstance(n,ast.BinOp) and type(n.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div):
            a,b=visit(n.left),visit(n.right)
            return {ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,ast.Div:lambda:a/b}[type(n.op)]()
        raise ValueError('unsupported expression')
    return visit(tree.body)

class Adjudicator:
    def __init__(self, collective):
        self.collective=collective; self.db=collective.db
        with self.db: self.db.execute('CREATE TABLE IF NOT EXISTS adjudication(id TEXT PRIMARY KEY, report TEXT NOT NULL)')
    def prepare(self, report_id):
        source=self.collective.get(report_id)
        if source['status'] not in ('complete','partial'): raise ValueError('unfinished report')
        expected=evaluate(source['question'])
        findings=[]
        for attempt in source['attempts']:
            if 'record' not in attempt: continue
            row=self.db.execute('SELECT question,result,provenance FROM research WHERE id=?',(attempt['record'],)).fetchone()
            if row is None or row[0]!=source['question']: raise ValueError('missing or mismatched record')
            answer=row[1]; status='unparseable'
            if row[2]=='demo': status='demonstration'
            elif len(answer)<=128 and re.fullmatch(r'[+-]?\d+(?:/\d+|\.\d+)?',answer.strip()):
                try: status='correct' if Fraction(answer.strip())==expected else 'incorrect'
                except (ValueError,ZeroDivisionError): pass
            findings.append(dict(record=attempt['record'],original=answer,status=status))
        result=dict(id=str(uuid.uuid4()),source=report_id,expression=source['question'],conclusion=str(expected),findings=findings,classification='local_arithmetic_check',authenticated=False,verifier='rational-v1')
        return result
    def insert(self, result):
        self.db.execute('INSERT INTO adjudication VALUES (?,?)',(result['id'],json.dumps(result)))
    def run(self, report_id):
        result=self.prepare(report_id)
        with self.db: self.insert(result)
        return result
    def get(self,rid):
        row=self.db.execute('SELECT report FROM adjudication WHERE id=?',(rid,)).fetchone()
        if row is None: raise KeyError(rid)
        return json.loads(row[0])
