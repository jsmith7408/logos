# Alpha 0.18 local release revalidation

2026-11-27. Main inspected at 26860b728fa9aa4974b994498d764260a2f95671.

Local Alpha 0.18 archive extracted; `sha256sum -c SHA256SUMS` passed all 135 entries. `python -m unittest discover` completed 73 tests in 27.345 seconds, OK. Compared with Alpha 0.17 archive: eight new or changed files (ALPHA17_SHA256SUMS.historical, dashboard.py, INCREMENT.md, SHA256SUMS, test_claim_workflow.py, ALPHA17_INCREMENT.md, v6_tests_18.txt, claim_workflow.py); no removed files, excluding Python caches.

This report is not publication of the full Alpha 0.18 source. No live provider, independent scientific validation or external security certification was performed. V5 remains owner-authorized. Next: transfer exact Alpha 0.18 release bytes and verify remote manifest before merging release.
