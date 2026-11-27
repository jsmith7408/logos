# V6 Alpha 0.4 — atomic workflow persistence
Recovered Alpha 0.3, foundation and V5 master locally; all seven prior ZIPs passed unzip integrity tests. Remote repository not accessed. V5 remains owner-authorized, not independently certified.

Alpha 0.3 committed research before linking it to a workflow step, permitting orphan records after failure. Now research insertion, step completion and final run completion share a SQLite transaction. Provider calls occur outside that transaction. Offline recovery marks running runs and steps interrupted, preserves completed steps and is idempotent. Stop ALL workers before invoking Workflow.recover_interrupted(); it does not detect live workers or resume calls. The workflow now uses Core.prepare/insert directly, so custom Application.investigate overrides are not used by workflow execution. Provider side effects cannot be rolled back. No hard provider timeout or response cap yet. No actual crash/power-loss experiment: tests inject SQLite statement failures.

Executed 18 V6 tests and 70 inherited V5 test executions successfully; inherited counts may include duplicates. No paid API calls, live inference or public deployment. Independent scientific and security evaluation outstanding.

Run: python -m unittest -v; then (cd v5 && python -m unittest discover -v). Python 3.10+ and cryptography required. Next: bounded local provider adapter, safe worker lifecycle and dashboard.
