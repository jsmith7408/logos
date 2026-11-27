# Project LOGOS

Evidence-gated applied intelligence research: local reasoning workflows, model-independent provider adapters, persistent research records, collective comparison, deterministic arithmetic and symbolic inference, and explicit uncertainty preservation.

## Latest consolidated source: V6.0 Alpha 0.21

- [Alpha 0.21 source and application](v6/releases/alpha-0.21/)
- [Local installation and use](v6/releases/alpha-0.21/README.md)
- [Development report](v6/releases/alpha-0.21/INCREMENT.md)
- [Native knowledge and inference engine](v6/releases/alpha-0.21/knowledge.py)
- [Conflict isolation tests](v6/releases/alpha-0.21/test_scoped.py)
- [V6 regression execution log](v6/releases/alpha-0.21/v6_tests_21.txt)
- [SHA-256 content manifest](v6/releases/alpha-0.21/SHA256SUMS)
- [Previous release: Alpha 0.20](v6/releases/alpha-0.20/)

Alpha 0.21 adds opt-in conflict-isolated native deduction (`infer-local:`), preserving strict global checking (`infer:`). Relevant contradictions block conclusions; unrelated contradictions are isolated. Persistent structured facts and rules support provider-independent symbolic deduction.

## Status and limitations

The preserved local V6 regression report records **86/86 tests passed**, including four new tests. These are local regression results, not independently performed GitHub CI or scientific benchmarks. No fresh regression execution occurred during publication.

V5.0 is an **owner-authorized release**, not independent scientific validation or external security certification. Independent held-out evaluation, live-provider validation and external security assessment remain outstanding. Premises are not authenticated, dependency mapping is conservative, and this is a local single-user prototype, not a production-deployed autonomous system. Hashes do not establish authentic or independent corroboration.

Earlier [V6 foundation](v6/README.md) and [V5 acceptance limitations](v5/ACCEPTANCE.md) are preserved.
