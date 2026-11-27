# LOGOS V6 Alpha 0.5
Local Python application; Python 3.10+ and cryptography required. Install cryptography in a virtual environment if absent. Run `python -m unittest -v` and `(cd v5 && python -m unittest discover -v)` from the extracted directory. See INCREMENT.md for current changes and limitations. Core(path) stores SQLite research; Application(core, bridge) separates unverified research from authenticated V5 comparisons. Workflow(application).run(questions, provider) executes bounded plans. DemoProvider is not AI inference. Offline maintenance: stop all workers, then call Workflow(application).recover_interrupted(). No dashboard yet; local provider adapter is fixture-tested only. Do not expose publicly; database is mutable and OS isolation is incomplete. V5 owner acceptance is not independent certification.

## Alpha 0.5 local provider
With an already installed Ollama server and local model, use `from providers import OllamaProvider` and pass `OllamaProvider('your-installed-model')` to `Workflow(application).run(['question'], provider)`. Only IPv4 loopback is supported. No model installation or remote API is performed by LOGOS. Run `python -m unittest -v` for fixture tests. See INCREMENT.md for timeout limitations. Do not expose publicly.

## Alpha 0.6 deadline worker
Use `from worker import DeadlineProvider` and wrap `OllamaProvider('your-installed-model')` with `DeadlineProvider(provider, deadline=35)` before passing it to Workflow.run. The subprocess timeout includes communication but OS process creation and cleanup may add latency. It does not cancel server-side inference or provide OS sandboxing. The wrapper is opt-in and currently supports only the Ollama adapter. Run `python -m unittest discover -v` to reproduce fixture tests.

## Alpha 0.7 dashboard
Run `python dashboard.py --db research.sqlite` and open http://127.0.0.1:8765 in your local browser. Demo mode requires no model. For Ollama, enter the name of an already installed local model. Up to five questions per run; each Ollama step uses a 35-second client worker deadline. Stop with Ctrl+C. The dashboard is synchronous and intended for a trusted single-user machine; do not expose it via proxies or tunnels. It does not expose evidence submission or authentication management. Existing V5 bridge remains available through Python. Run `python -m unittest discover -v` for HTTP and other tests.

## Alpha 0.8 collective comparison
Use `Collective(application).run('question', {'first': provider1, 'second': provider2})` after importing `Collective` from `collective`. Use deadline-wrapped local providers for bounded client calls. Reports are stored in the same SQLite database; retrieve with `Collective(application).get(report_id)`. Exact agreement is not verification; text difference is not necessarily contradiction. No automatic correction or evidence promotion. Run `python -m unittest test_collective -v` for fixture tests. See INCREMENT.md for limitations.

## Alpha 0.9 arithmetic adjudication
After a collective run on a bare arithmetic expression (e.g. `1/2+1/3`), call `Adjudicator(collective).run(report['id'])` after importing from `adjudication`. Results are stored separately and can be retrieved using `get(id)`. Only integer arithmetic and plain numeric provider answers are supported; unsupported expressions fail closed. Run `python -m unittest test_adjudication -v`. Local checks do not pass the V5 authentication gate.

## Alpha 0.10 selective correction
Import `Correction` from `correction`, then call `Correction(collective).run(report_id)` on a completed supported arithmetic investigation. Retrieve persisted decisions using `get(id)`. Original records are not overwritten. Run `python -m unittest test_correction -v`. This is deterministic arithmetic correction, not learned strategy selection or authenticated evidence. See INCREMENT.md.

## Alpha 0.11
Run `python dashboard.py` and open http://127.0.0.1:8765. The Collective arithmetic form accepts integer expressions with +, -, *, / and parentheses. Select demonstration or two installed Ollama model names. Demo responses are not treated as verified provider answers. Reports remain unauthenticated; V5 submission is separate. Run `python -m unittest discover -v` and `(cd v5 && python -m unittest discover -v)` to reproduce tests. Use only on a trusted local computer.

## Alpha 0.12
Use `Strategy(application).run('1/3+1/6')` from strategy.py for exact arithmetic without inference; unsupported questions require a provider roster. Optional budget is supported only for DeadlineProvider and DemoProvider. Dashboard collective calls use a 70-second aggregate client budget. Offline recovery: stop all writers, then call `Collective(application).recover_interrupted()`; interrupted investigations are marked, not replayed. Strategy reports are stored in `strategies`. Run `python -m unittest test_strategy -v`. See INCREMENT.md for limitations.

## Alpha 0.13
The Adaptive research form on the local dashboard selects exact arithmetic or unverified collective research and displays persisted strategy reports. Select demonstration mode for offline testing; Ollama mode requires both model names even for exact arithmetic. Run `python -m unittest test_adaptive_dashboard -v` for HTTP integration tests. The interface is synchronous and intended for trusted local use only. No semantic truth verification is implied.

## Alpha 0.14
Submit a collective investigation ID in the Structured claim comparison form. Provider responses must be JSON arrays of 1–10 objects with exactly subject, predicate, object, scope (nonempty strings), and polarity (boolean). Example: `[{"subject":"A","predicate":"is","object":"B","scope":"2026","polarity":true}]`. Use the adaptive research form with a question requesting this schema, then copy its collective source ID. Only exact matching scoped tuples are compared; different tuples remain undetermined. Reports preserve original record IDs and never establish truth or authenticate evidence. Run `python -m unittest test_claims -v`. Demo mode cannot generate valid claims.

## Alpha 0.15
Use the Evidence snapshots form to attach a source label, excerpt and reported stance to a claim report ID and zero-based claim index. No URLs are fetched. All records remain user_supplied_unverified. In Python, `Evidence(collective).compare(report_id, index)` returns up to 100 latest records and a reported conflict flag; truncation is explicit. SHA256 identifies snapshot content but is not a signature. Run `python -m unittest test_evidence -v`. SQLite JSON functions are required. Independent verification remains outstanding.

## Alpha 0.16 — Inspecting evidence integrity
The local dashboard has a new **Evidence inspection** form. Enter a structured claim report ID and zero-based claim index; LOGOS displays up to 100 recent evidence records, reported opposition, repeated snapshots, stored SHA-256 mismatches, and claim-snapshot mismatches. Excerpts and labels are escaped for browser display. You can also call `Evidence(collective).inspect(report_id,index,limit=100)` from Python. The previous Alpha 0.15 fingerprint encoding is preserved for backwards compatibility. These checks detect ordinary/incomplete modifications; an attacker with database write access can replace both evidence and fingerprints. Duplicate snapshots are not counted as independent corroboration. Never promote these records into authenticated V5 evidence. Run `python -m unittest test_evidence_integrity -v`; run `python -m unittest discover -v` and `cd v5 && python -m unittest discover -v` for full regressions. GitHub synchronization status is recorded separately from local release status. No public deployment and no paid API use.

## Alpha 0.17
Evidence inspection now reports candidate dependency groups; distinct groups do not establish independence. See INCREMENT.md.

Alpha 0.21: use Strategy.knowledge.fact(literal, source), .rule(premises, conclusion), and Strategy.run("infer:A", native_only=True). Explicit propositional literals only; ! denotes negation. All assertions are unauthenticated.

## Alpha 0.22 — Native research planner
Use `p = Strategy(application).planner`, `oid = p.create('C')`, `report = p.run(oid, max_checks=8, inference_budget=1000)`, and `p.get(report['id'])`. Store explicit facts and rules through Strategy.knowledge first. Arithmetic objectives route to exact arithmetic; literals route to scoped inference; other questions abstain. Conditional hypotheses are not authenticated facts. See INCREMENT.md and run `python -m unittest test_planner -v`.

## Alpha 0.23 — Investigation continuation
Use `p.history(oid, limit=20)` and `p.resume(oid, max_checks=8, inference_budget=1000)` to revisit a persistent objective after knowledge changes or restart. Prior reports remain intact; the new report links its predecessor. This is bounded re-evaluation, not automatic evidence acquisition. Run `python -m unittest test_resume -v`.
