# Alpha 0.16 — Evidence integrity and duplicate-aware inspection

## Recovery
Recovered complete Alpha 0.15 local tree and archive; checked inherited manifest and ZIP CRC. Located and CRC-tested standalone V6 foundation and V5 master archives. Remote GitHub `jsmith7408/logos` was accessed and confirmed writeable; main currently carries only early V6 source, so this version's complete local archive is the canonical source snapshot unless remote synchronization is fully verified.

## Changes
- Evidence.inspect adds bounded (1–100) snapshot examination with historical SHA-256 recomputation, relation-to-current-claim comparison, exact repeated-source/excerpt/stance detection, and unverified reported-conflict indication based on intact entries.
- Preserves preexisting Alpha 0.15 snapshot fingerprint encoding, and does not mutate original evidence.
- Dashboard exposes token-protected `/evidence-inspect`, escapes source text and shows explicit authentication warnings.
- Added regression tests for duplicate/conflicting evidence, tampering, invalid bounds, HTML injection and missing CSRF token.

## Limits and negative findings
- Database writer can recalculate a forged fingerprint; SHA-256 is not a signature or independent authentication.
- Duplicate labels do not imply real-world source identity, and nonduplicates do not imply independent sources.
- No external source validation, live AI inference, automatic semantic entailment, full OS sandbox, or production deployment.
- Independent held-out ordinary-versus-LOGOS evaluation and external security certification remain uncompleted. V5.0 stays owner-authorized only.

## Actual regression execution (2026-11-27)
- `python -m unittest discover -v`: 68/68 passed (28.764 seconds; updated run).
- `(cd v5 && python -m unittest discover -v)`: 70/70 passed (2.064 seconds; inherited V5 cases include duplication).
- Four new Alpha 0.16 tests passed. No independent held-out model comparison, model inference or external security testing occurred.
- GitHub publication is a separate deployment action. Final remote commit/PR status must be verified independently of this local artifact.
