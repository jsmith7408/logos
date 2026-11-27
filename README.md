# Project LOGOS

## Current source: V6.0 Alpha 0.29 — own-weight contextual language intelligence

Owner policy: **no third-party AI inference**, including locally hosted pretrained models and commercial AI services. Web access is for evidence retrieval only. The supported entry point is the native CLI; historical provider instructions are superseded.

- [Current V6 source](v6/)
- [Versioned release](v6/releases/alpha-0.29/)
- [Installation and usage](v6/README.md)
- [Development and limitations](v6/INCREMENT.md)
- [Own-weight language engine](v6/language29.py)
- [Native CLI](v6/logos_native.py)
- [Network policy](v6/network29.py)
- [Reproducible experiment](v6/language_experiment29.py) and [results](v6/language_experiment_29.json)
- [Regression tests](v6/test_language29.py)
- [V6 test log](v6/v6_tests_29.txt) and [V5 test log](v6/v5_tests_29.txt)
- [Live web probe](v6/web_probe_29.txt)
- [Integrity manifest](v6/SHA256SUMS)
- [Previous release](v6/releases/alpha-0.28/)

Alpha 0.29 introduces a two-token context neural language model with trainable eight-dimensional embeddings, cross-entropy and backpropagation implemented in standard-library Python. Explicitly reviewed text, persistent candidate checkpoints, operator activation and rollback, distributional similarity, restricted native conversation, and tightened document-host retrieval policy. **160/160 V6 and 70/70 inherited V5 test executions passed locally.** No pretrained weights or third-party inference. Synthetic training loss 2.39945 to 0.14840; unfamiliar recombination loss 4.15873 and repetitive generation demonstrate poor generalization. Live DNS probe failed.

## Limitations

This is not a general-purpose language model. Training loss is not a held-out regression gate. Text review is permission to learn language patterns, not evidence authentication. No automatic fact promotion. Network policy is not an OS sandbox; legacy fixture interfaces remain in trusted Python. No independent scientific or security certification. V5 remains owner-authorized. See development report for full bounds.
