"""Restricted exact arithmetic; no execution of input as code."""
import ast
import operator
from fractions import Fraction

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

def evaluate(source):
    if type(source) is not str or not 0 < len(source) <= 256:
        raise ValueError('expression length')
    tree = ast.parse(source, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 64:
        raise ValueError('node budget')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            value = Fraction(node.value)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
            value = OPS[type(node.op)](visit(node.left), visit(node.right))
        else:
            raise ValueError('unsupported expression')
        if max(value.numerator.bit_length(), value.denominator.bit_length()) > 512:
            raise ValueError('result budget')
        return value
    return visit(tree.body)

def solve(source):
    try:
        return {'status': 'solved', 'answer': str(evaluate(source)), 'confidence': None}
    except (ValueError, SyntaxError, ZeroDivisionError, RecursionError):
        return {'status': 'abstain', 'confidence': None}
