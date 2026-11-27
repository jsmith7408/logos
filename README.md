# Project LOGOS

## Current source: V6.0 Alpha 0.30 — native attention and generalization gate

Owner policy: **no third-party AI inference or pretrained weights**. Web access is for evidence retrieval only. The supported entry point is the native CLI; historical provider instructions are superseded. Do not install or configure external AI providers for LOGOS.

- [Current V6 source](v6/)
- [Versioned release](v6/releases/alpha-0.30/)
- [Native installation and usage](NATIVE.md) · [Historical V6 instructions](v6/README.md)
- [Development and limitations](v6/INCREMENT.md)
- [Native attention engine](v6/language30.py)
- [Native CLI](v6/logos_native.py)
- [Reproducible experiment](v6/language_experiment30.py) and [results](v6/language_experiment_30.json)
- [Regression tests](v6/test_language30.py)
- [V6 test log](v6/v6_tests_30.txt) and [V5 test log](v6/v5_tests_30.txt)
- [Integrity manifest](v6/SHA256SUMS)
- [Previous release](v6/releases/alpha-0.29/)

Alpha 0.30 implements four-token context, 12-dimensional embeddings, learned-position dot-product attention, a 16-unit hidden layer, analytical backpropagation, training-only vocabulary with character fallback, three approved corpus splits, validation-based early stopping and explicit checkpoint admission/rollback. **168/168 V6 and 70/70 inherited V5 test executions passed locally.** Eight new tests include numerical gradient checks and deliberately defective checkpoint rejection. Synthetic test loss fell from 3.33129 to 2.04834 against randomly initialized Alpha 0.30; no comparable Alpha 0.29 superiority claim. Output remains repetitive. No external model inference.

## Limitations

Tiny related synthetic corpus, not independent external evaluation. Test split is used for admission; repeated use can contaminate evaluation. Exact duplicate rejection cannot exclude passage overlap. Earlier experimental routes do not inherit the new checkpoint gate. No automatic fact promotion or secure untrusted-database authorization. Live web access remains unverified (previous DNS failure; no new live probe in this cycle). No OS network isolation or independent scientific/security certification. V5 is owner-authorized. See development report for bounds.
