"""Pure candidate admission policy; no automatic activation."""
import math


def admit(baseline, candidate, *, max_latency_ratio=1.2):
    """Compare matched validation measurements; fail closed on invalid data."""
    keys = {'loss_per_byte', 'latency_ms', 'regressions'}
    for record in (baseline, candidate):
        if set(record) != keys:
            raise ValueError('measurement schema')
        for key in keys:
            value = record[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('invalid measurement')
        if record['latency_ms'] <= 0 or type(record['regressions']) is not int:
            raise ValueError('invalid latency or regression count')
    if type(max_latency_ratio) not in (int, float) or not math.isfinite(max_latency_ratio) or not 1 <= max_latency_ratio <= 2:
        raise ValueError('latency policy')
    reasons = []
    if baseline['regressions'] or candidate['regressions']:
        reasons.append('regression failure')
    if candidate['loss_per_byte'] >= baseline['loss_per_byte']:
        reasons.append('no strict loss improvement')
    if candidate['latency_ms'] / baseline['latency_ms'] > max_latency_ratio:
        reasons.append('latency budget exceeded')
    return not reasons, tuple(reasons)
