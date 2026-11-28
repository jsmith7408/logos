"""Strict JSON boundary for the mathematical dispatcher."""
import json
from stage2_unified import dispatch

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result

def reject_constant(value):
    raise ValueError('nonfinite JSON constant')

def run_json(source):
    if type(source) is not str or len(source) > 65536:
        return {'status':'abstain','confidence':None}
    try:
        return dispatch(json.loads(source, object_pairs_hook=pairs, parse_constant=reject_constant))
    except (ValueError, RecursionError):
        return {'status':'abstain','confidence':None}
