# V5 foundation dependency audit

Inspected cleanup checkpoint 13b6ee0aa665daaf3d0ff3483f8d9620d7622a1c. Root v5 and v6/v5 share 20 identical Git blobs by filename. Four differ: FINAL_SHA256SUMS, regression_04.txt, regression_current.txt, tests.txt. Root-only: README.md, requirements.txt.

v6/bridge.py explicitly executes its sibling v5/service.py using sys.executable and fails closed on subprocess errors. Removing nested v5 would break this route. Preserve both directories and their manifests until a canonical migration is tested, including standalone release packaging, authenticated comparisons, fail-closed behavior and inherited regressions. No source deletion or certification. V5 is owner-authorized only.

Legacy provider interfaces were previously inspected and reject inference; Core accepts a generic Provider protocol and invokes reason(), so repository-wide external inference exclusion is not established by the two disabled adapters alone. Audit callers before changing compatibility interfaces.
