# Project LOGOS

Evidence-gated local applied intelligence research: native reasoning, persistent investigations, bounded workflows, optional local model adapters, and explicit uncertainty.

## Latest consolidated source: V6.0 Alpha 0.24

- [Current V6 source](v6/) — mirrors the release snapshot
- [Versioned release](v6/releases/alpha-0.24/)
- [Installation and use](v6/README.md)
- [Development report](v6/INCREMENT.md)
- [Evidence lifecycle](v6/verified.py) and [regression tests](v6/test_attestation_lifecycle.py)
- [V6 test log](v6/v6_tests_24_consolidated.txt) and [V5 test log](v6/v5_tests_24_consolidated.txt)
- [SHA-256 manifest](v6/SHA256SUMS)
- [Original V6 foundation](v6/foundation/)

Alpha 0.24 includes revalidated HMAC attestations, persistent trust metadata, explicit key reload and revocation, controlled premise promotion and withdrawal, a bounded relationship graph, and automatic queued research continuation. The earlier continuation and acquisition variants remain preserved. **119/119 V6 and 70/70 inherited V5 regression executions passed locally.** Run the tests and verify the manifest from v6/ or the release directory.

## Limitations

The local Ollama smoke test could not run because the service was unavailable. No actual live model validation, external evidence collection, proof of source independence, calibrated reliability, independent held-out scientific comparison or external security certification. Trust metadata and manual facts are local and mutable; only a trusted single-user process is supported. V5 remains owner-authorized, not independently certified. No public deployment or paid API. See [V5 acceptance](v5/ACCEPTANCE.md), [full report](v6/INCREMENT.md), [previous continuation release](v6/releases/alpha-0.23/) and [acquisition variant](v6/releases/alpha-0.23-acquisition/). The original Alpha 0.24 snapshot remains in commit 31ceda02c5a976f5d780e73ba6f31408655cebfb.
