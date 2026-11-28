"""Exact finite probability and binary Bayesian updates."""
from fractions import Fraction

def probability(op, values):
    if type(values) is not list or len(values)>128 or any(type(x) is not Fraction or not 0<=x<=1 or max(x.numerator.bit_length(),x.denominator.bit_length())>512 for x in values):
        raise ValueError('probability domain')
    if op=='conditional' and len(values)==2:
        joint,evidence=values
        if joint>evidence: raise ValueError('joint exceeds evidence')
        if not evidence: return {'status':'undefined','confidence':None}
        answer=joint/evidence
    elif op=='bayes' and len(values)==3:
        prior, likelihood, alternative=values
        joint=prior*likelihood
        evidence=joint+(1-prior)*alternative
        if not evidence: return {'status':'undefined','confidence':None}
        answer=joint/evidence
    elif op=='distribution' and values:
        return {'status':'valid' if sum(values)==1 else 'invalid','confidence':None}
    else: raise ValueError('operation or arity')
    return {'status':'solved','answer':str(answer),'confidence':None}
