# Project LOGOS

## Current source: V6.0 Alpha 0.28 — self-contained native research

Owner policy: **no third-party AI inference**, including Ollama or commercial AI systems. Web access is for evidence retrieval, not inference services. The current known Ollama adapter and worker fail closed; historical releases are preserved but their provider instructions are superseded. Use the native-only CLI.

- [Current V6 source](v6/)
- [Versioned release](v6/releases/alpha-0.28/)
- [Installation and usage](v6/README.md)
- [Development and limitations](v6/INCREMENT.md)
- [Native CLI](v6/logos_native.py)
- [Native research engine](v6/native_research.py)
- [Public HTTPS evidence retrieval](v6/web_evidence.py)
- [Executed experiment](v6/native_experiment_28.json)
- [Regression tests](v6/test_native28.py)
- [V6 test log](v6/v6_tests_28.txt) and [V5 test log](v6/v5_tests_28.txt)
- [Live web probe](v6/web_probe_28.txt)
- [Integrity manifest](v6/SHA256SUMS)
- [Previous release](v6/releases/alpha-0.27/)

Native typed composition, exact Bayesian updates, persistent hypothesis records, bounded question generation and experimental cycles, external benchmark import, and a small own-corpus statistical bigram language model. Web snapshots are unverified and quarantined. **151/151 V6 and 70/70 inherited V5 test executions passed locally.** Nine native research tests added, ten legacy adapter tests replaced with three policy/validation tests. No live third-party AI inference executed. Live web probe failed DNS resolution; fixture retrieval tests passed.

## Limitations

Not a general-purpose LLM, general causal inference engine or independently validated intelligence system. Imported labels and web source independence are not authenticated. No autonomous policy activation in the new research cycle. Current supported entry point has no model provider arguments, but trusted local Python retains legacy fixture interfaces; this is not an operating-system egress sandbox. No independently established scientific or security certification; V5 remains owner-authorized. See the development report for full bounds and residual limitations.
