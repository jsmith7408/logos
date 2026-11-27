# Meta-cognitive Reasoning Framework (LOGOS-compatible)

## Goal
Provide a thin observational layer that lets a local reasoning system inspect its own recent activity, conflict patterns, and resource use without altering the underlying knowledge base or treating any observation as authenticated.

## Principles
1. **Observation only** — the framework records and summarizes; it does not rewrite facts or rules.
2. **Explicit uncertainty** — every report carries `authenticated=False`.
3. **Bounded** — queries and reports are limited in size and scope.
4. **Composable** — designed to sit beside Strategy, Knowledge, and Collective rather than replace them.
5. **Local** — uses the same SQLite connection already employed by the kernel.

## Functional layers

### Perception
Captures raw outcomes:
- Strategy classification and proof status
- Collective comparison result
- Inference step count and budget exhaustion
- Elapsed time and provider attempt count

### Appraisal
Aggregates observations:
- Strategy type distribution
- Conflict frequency and recent conflict list
- Recurring text_difference patterns
- Resource warnings (step count, elapsed time, database growth)

### Reflection
Produces a structured report containing:
- period summary
- conflict highlights
- distribution of reasoning paths used
- snapshot of knowledge-base size
- advisory notes (never automatic actions)

### Optional advisory actions (human- or higher-layer gated)
Examples of notes the framework may surface (but never execute):
- “Literal X has triggered conflict N times; consider isolation or review.”
- “Collective text_difference rate is high on arithmetic questions; prefer native evaluation.”
- “Budget exhausted on large dependency cones; reduce rule set or raise budget.”

## Interface sketch
```python
monitor.record_strategy(strategy_report)
monitor.record_collective(collective_report)
monitor.record_infer(evidence_dict)
snapshot = monitor.snapshot()
conflicts = monitor.conflicts(limit=20)
report = monitor.report()          # persists and returns the reflection
```

## Relationship to existing LOGOS components
| LOGOS component     | Monitor interaction                  |
|---------------------|--------------------------------------|
| Strategy            | record_strategy after each run       |
| Knowledge.infer     | record_infer on the returned evidence|
| Collective          | record_collective after each run     |
| Core / SQLite       | shared connection, read-only queries |
| Dashboard           | optional new section for latest reflection report |

## Limits
- No semantic understanding of literals beyond string identity.
- No automatic conflict resolution.
- No external knowledge or web access.
- Single-user, local scope.
- Reports are observational artifacts, not evidence.

This framework supplies the minimal reflective loop needed to begin examining a system’s own reasoning traces while remaining inside the conservative design already established by the LOGOS kernel.
