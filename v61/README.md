# LOGOS V6.1 integration candidate

From the repository root, run:

    python -m pip install -r v5/requirements.txt
    python -m unittest v61.test_engine -v

Engine composes V6 Core with V5's allowlisted signed-comparison service via a local subprocess. It stores the comparison request and digest before invoking the gate. Successful comparisons are candidate evidence, never verified facts; linked research IDs are associations, not proof. Provider responses remain demo or unverified. Gate failures are indeterminate, not successful. A crash can leave an attempt pending; do not blindly retry because the separate gate database may already have consumed the evidence. The two databases are not transactionally atomic across processes.

Threat model: trusted local runtime and filesystem. This is not a sandbox or immutable audit log. Raw comparison inputs are stored locally in plaintext; protect both databases and backups. Keep signing keys outside the repository. No independent inference, external certification, remote API or automated knowledge promotion. Tests use synthetic signed fixtures, not real model results. V5 and V6 remain unchanged.

Local test run: six new integration tests passed; legacy suite rerun was interrupted by the execution timeout. CI results are pending.
