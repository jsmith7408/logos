"""Bounded exact rational linear-system solver."""
from fractions import Fraction

def solve_system(rows):
    if type(rows) not in (list, tuple) or not 1 <= len(rows) <= 16:
        raise ValueError('row budget')
    if type(rows[0]) not in (list, tuple) or not 2 <= len(rows[0]) <= 17:
        raise ValueError('column budget')
    n = len(rows[0])-1
    def bounded(x):
        if max(x.numerator.bit_length(), x.denominator.bit_length()) > 512:
            raise ValueError('rational budget')
        return x
    a = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != n+1:
            raise ValueError('shape')
        if any(type(x) not in (int, Fraction) for x in row):
            raise ValueError('exact inputs required')
        a.append([bounded(Fraction(x)) for x in row])
    original = [r[:] for r in a]
    pivots = []
    for c in range(n):
        k = len(pivots)
        p = next((i for i in range(k,len(a)) if a[i][c]), None)
        if p is None:
            continue
        a[k], a[p] = a[p], a[k]
        d = a[k][c]
        a[k] = [bounded(x/d) for x in a[k]]
        for i in range(len(a)):
            if i != k:
                d = a[i][c]
                a[i] = [bounded(x-d*y) for x,y in zip(a[i],a[k])]
        pivots.append(c)
    if any(not any(r[:-1]) and r[-1] for r in a):
        return {'status':'inconsistent'}
    if len(pivots) < n:
        return {'status':'underdetermined'}
    x = [a[i][-1] for i in range(n)]
    if any(sum(v*w for v,w in zip(r[:-1],x)) != r[-1] for r in original):
        raise ArithmeticError('verification failed')
    return {'status':'unique','solution':[str(v) for v in x]}
