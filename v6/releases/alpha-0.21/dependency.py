"""Conservative grouping of reported evidence; never establishes independence."""
import unicodedata

def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())

def dependency_groups(records):
    valid = [r for r in records if r['fingerprint_matches'] and r['claim_snapshot_matches'] and all(isinstance(r.get(k), str) and r[k].strip() for k in ('source','excerpt'))]
    parent = list(range(len(valid)))
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    seen = {}
    for i, r in enumerate(valid):
        for field in ('source','excerpt'):
            key = (field, normalize(r[field]))
            if key in seen:
                parent[root(i)] = root(seen[key])
            else:
                seen[key] = i
    groups = {}
    for i, r in enumerate(valid):
        groups.setdefault(root(i), []).append(r['id'])
    return dict(groups=list(groups.values()), eligible_records=len(valid), excluded_records=len(records)-len(valid), candidate_group_count=len(groups), independence_established=False, disclaimer='Matching normalized labels or excerpts suggest possible dependency only; distinct groups do not prove independence.')
