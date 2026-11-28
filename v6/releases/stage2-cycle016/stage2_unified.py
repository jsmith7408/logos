"""Explicit operation dispatch with bounded JSON-compatible inputs."""
import json
from fractions import Fraction
import stage2_math_v2 as math
import stage2_algebra as algebra
import stage2_matrix as matrix
import stage2_poly as poly
from stage2_logic import entail
from stage2_predicate import check
from stage2_rules import infer
from stage2_induction import hypothesize
from stage2_probability import probability
from stage2_causal import causal

def exact(v):
    if type(v) is int and v.bit_length() <= 512:
        return Fraction(v)
    if type(v) is str and len(v) <= 256:
        return math.evaluate(v)
    raise ValueError('exact coefficient required')

def vector(v, limit=17):
    if type(v) is not list or not 1 <= len(v) <= limit:
        raise ValueError('vector budget')
    return [exact(x) for x in v]

def dispatch(request):
    try:
        if type(request) is not dict or set(request) != {'operation','input'}:
            raise ValueError('request schema')
        op, v = request['operation'], request['input']
        if op == 'causal':
            if type(v) is not dict or set(v) != {'model','intervention','query'}: raise ValueError('causal schema')
            result = causal(v['model'],v['intervention'],v['query'])
        elif op == 'probability':
            if type(v) is not dict or set(v) != {'kind','values'}: raise ValueError('probability schema')
            result = probability(v['kind'],vector(v['values'],128))
        elif op == 'induction': result = hypothesize(v)
        elif op == 'rules':
            if type(v) is not dict or set(v) != {'facts','rules','query'}: raise ValueError('rule schema')
            result = infer(v['facts'],v['rules'],v['query'])
        elif op == 'predicate':
            if type(v) is not dict or set(v) != {'model','formula'}: raise ValueError('predicate schema')
            result = check(v['model'],v['formula'])
        elif op == 'entail':
            if type(v) is not dict or set(v) != {'premises','conclusion'}: raise ValueError('logic schema')
            result = entail(v['premises'],v['conclusion'])
        elif op == 'arithmetic': result = math.solve(v)
        elif op == 'verify': result = math.verify_equation(v)
        elif op == 'linear': result = algebra.solve_linear(v)
        elif op == 'matrix':
            if type(v) is not list or not 1 <= len(v) <= 16:
                raise ValueError('row budget')
            result = matrix.solve_system([vector(r) for r in v])
        elif op == 'roots': result = poly.roots(vector(v))
        elif op == 'derivative': result = {'status':'solved','answer':[str(x) for x in poly.derivative(vector(v))]}
        else: raise ValueError('unsupported operation')
        return {**result, 'confidence': None}
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, RecursionError):
        return {'status':'abstain','confidence':None}

def run_json(source):
    if type(source) is not str or len(source) > 65536:
        return {'status':'abstain','confidence':None}
    try: return dispatch(json.loads(source))
    except (ValueError, RecursionError): return {'status':'abstain','confidence':None}

if __name__ == '__main__':
    import sys
    print(json.dumps(run_json(sys.stdin.read(65537))))
