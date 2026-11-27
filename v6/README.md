# Alpha 0.30 — Native attention and regression-gated language training

Current policy: no third-party AI inference or pretrained weights. Python standard library only. The new model uses a four-token window, 12-dimensional embeddings, content-dependent dot-product attention with learned position biases, a 16-unit tanh hidden layer, and softmax output. Training uses explicit analytical gradients and bounded SGD.

Use separately approved training, validation, and test documents:

```sh
python logos_native.py learn-context train.txt --source "reviewed training corpus" --split train --approve
python logos_native.py learn-context validation.txt --source "reviewed validation corpus" --split validation --approve
python logos_native.py learn-context test.txt --source "reviewed test corpus" --split test --approve
python logos_native.py train-context --epochs 24 --patience 4
python logos_native.py activate-context CHECKPOINT_ID --approve
python logos_native.py generate-context "logos learns"
python logos_native.py rollback-context --approve
python logos_native.py chat "calculate 2+2"
python language_experiment30.py
python -m unittest discover
(cd v5 && python -m unittest discover)
sha256sum -c SHA256SUMS
```

Vocabulary is learned from training only: frequent whole-word pieces with character fallback, not BPE. Separate normalized document fingerprints reject exact duplicate documents across splits; related passages can still overlap. Validation selects the best epoch; the test split participates in admission, so it is not an untouched independent benchmark after repeated use. Activation recomputes losses from the stored candidate and same dataset and requires improvement in train/validation and non-increase in test, compared with seeded initialization or the current active checkpoint. Explicit rollback restores the prior activation. Active corpus changes require a new database/evaluation protocol. Reviewed web excerpts may be added using `review-context-web SNAPSHOT_ID "exact excerpt" --split train --approve`; this is not fact authentication. Generated text is unverified and never used to add premises. Symbolic chat remains a separate restricted route. Earlier CLI commands are legacy experimental interfaces, not the new three-split gate. See INCREMENT.md for limitations.

## Previous release instructions (historical)

# Alpha 0.29 — Own-weight contextual language prototype

**Current policy:** no third-party AI inference, including GPT, Gemini, Grok, Claude, Meta or Ollama. No pretrained weights. Use the native CLI; historical provider instructions below are not operative.

Run these commands from this directory with Python 3 (standard library only). Use the same `--db` path before each subcommand if you want a database other than the default `research.sqlite`.

```sh
python logos_native.py learn corpus.txt --source "operator-reviewed local text" --approve
python logos_native.py train-neural --seed 29112601 --epochs 12
# Copy checkpoint ID from training report after reviewing it:
python logos_native.py activate-neural CHECKPOINT_ID --approve
python logos_native.py generate "logos learns"
python logos_native.py similar logos
python logos_native.py chat "calculate 2+2"
python logos_native.py chat "Does LOGOS support A?"
python logos_native.py fetch https://example.com/ --allow-host example.com
# Explicitly review an exact excerpt before adding it to language training:
python logos_native.py review-web SNAPSHOT_ID "exact text excerpt" --approve
python language_experiment29.py
python -m unittest discover
(cd v5 && python -m unittest discover)
sha256sum -c SHA256SUMS
```

Use `activate-neural` with an earlier retained ID to roll back. Training saves a candidate only; activation requires operator approval. This model learns two-token patterns, not general semantic understanding or factual truth. Lower training loss alone is not proof of improvement on new text. See `INCREMENT.md` and `language_experiment_29.json` for the negative generalization result and remaining limitations. Web GET requests are restricted to document hosts in `network29.py` plus the operator allowlist, and live DNS is still unavailable in the execution environment. This policy is not an OS-level sandbox. All generated text remains unverified; no automatic fact promotion. No third-party model calls.

## Historical instructions (superseded where inconsistent)

# Alpha 0.28 — self-contained native runtime

**Current policy:** no third-party AI inference, including locally hosted Ollama or commercial AI APIs. The old adapter and subprocess worker fail closed. The previous provider instructions below are historical and no longer operative. The fixture-only legacy interfaces are retained for regression reproduction; do not supply arbitrary provider objects. Use `logos_native.py` as the supported native-only entry point. No general-purpose LLM is included.

- `python logos_native.py status`
- `python logos_native.py objective C` then `python logos_native.py cycle`
- `python logos_native.py train corpus.txt` then `python logos_native.py predict logos` (in-house bigram model trained from bounded local text; outputs unverified)
- `python logos_native.py solve '{"domain":"probability","prior":"1/3","likelihood":"3/4","alternative":"1/4"}'`
- `python logos_native.py benchmark cases.json --source "dataset provenance"` (JSON array of `{"task":...,"expected":...}`; labels and claimed independence remain unverified)
- `python logos_native.py fetch https://example.com/ --allow-host example.com` (operator-authorized HTTPS text GET; no redirects, queries, credentials or private addresses; bounded snapshots remain quarantined)
- `python -m unittest discover` and `(cd v5 && python -m unittest discover)`; verify `sha256sum -c SHA256SUMS`.

See INCREMENT.md for limits. Historical guidance follows.

---

# LOGOS V6 Alpha 0.24 — consolidated
Local Python application; Python 3.10+ and cryptography required. Install cryptography in a virtual environment if absent. Run `python -m unittest -v` and `(cd v5 && python -m unittest discover -v)` from the extracted directory. See INCREMENT.md for current changes and limitations. Core(path) stores SQLite research; Application(core, bridge) separates unverified research from authenticated V5 comparisons. Workflow(application).run(questions, provider) executes bounded plans. DemoProvider is not AI inference. Offline maintenance: stop all workers, then call Workflow(application).recover_interrupted(). See the dashboard and current evidence-lifecycle instructions below; local provider adapter is fixture-tested only. Do not expose publicly; database is mutable and OS isolation is incomplete. V5 owner acceptance is not independent certification.

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

## Alpha 0.23
Use `strategy.acquisition.extract('Oak is a Tree', 'source')` to store an unauthenticated candidate. Optional `local_model=OllamaProvider('installed-model')` enables loopback fallback only. `strategy.planner.resume(objective)` rechecks current knowledge; `strategy.acquisition.prioritize()` ranks unresolved objectives. Live model validation remains pending.

## Alpha 0.24
See INCREMENT.md for attestation integration and limitations.

## Alpha 0.24 — consolidated evidence lifecycle
Current regression logs: `v6_tests_24_consolidated.txt` (119 passing) and `v5_tests_24_consolidated.txt` (70 passing inherited executions). Run `python -m unittest discover -v` and `(cd v5 && python -m unittest discover -v)` from this directory. Verify the release with `sha256sum -c SHA256SUMS`.

Use `strategy.verified.configure(source, key, origin, reliability="qualified")` to enroll a source, with a securely generated random key of at least 32 bytes. `reload(source, key)` restores an active persisted source after restart without writing the secret to SQLite. `revoke(source)` disables it. Sign the exact text using HMAC-SHA256 over `verified.payload(source, text)` and call `verified.acquire(source, text, signature)`. `verified.literal(record)` returns the corresponding native literal; `verified.assess(literal)` reports support/opposition and `verified.promote(literal)` explicitly approves an eligible premise. `verified.graph(limit=100)` returns bounded authenticated edges. Native inference refreshes attested facts before reading them; changes in eligibility automatically withdraw or restore previously approved premises. Mutation methods automatically resume up to eight affected research objectives (conservatively all objectives); `verified.continue_research(limit=8)` processes durable pending work. Use `strategy.run("infer-local:" + literal, native_only=True)` for provider-independent scoped inference. Existing unauthenticated manual facts/rules remain available and are not made authenticated by this feature.

Optional live smoke test: `python live_model_check.py YOUR_INSTALLED_MODEL` against a running local Ollama service. No model installation or external API is performed. The recorded run in `live_model_24.txt` was unavailable; actual local model validation remains pending. The current trust policy is a local configured-source prototype, not independent evidence of truth, external identity verification, secure key management or a production security assessment. See INCREMENT.md for bounds, concurrency and residual limitations.

## Alpha 0.25 — Reflective monitoring and native scheduling

`strategy.monitor.report(limit=100)` summarizes recent instrumented events (unauthenticated, observational only). `oid = strategy.planner.create('A')`; `jid = strategy.scheduler.schedule(oid, interval=3600, priority=5)`; call `strategy.scheduler.tick(limit=4)` from a trusted local process to run due native investigations. `strategy.scheduler.cancel(jid)` disables the job. No daemon or external providers are invoked by scheduling. See INCREMENT.md for limitations and design_inputs for the original supplied materials. Run `python -m unittest test_reflective_scheduler -v` or `python -m unittest discover -v`. See v6_tests_25.txt and v5_tests_25.txt for executed results.

## Alpha 0.26: controlled adaptive research

`Strategy(Application(core, None)).adaptive` exposes `reflect()`, `experiment('trim-v1', activate=False)`, explicit `experiment('trim-v1', activate=True)`, `rollback()`, `quarantine('A')`, `investigate('A')`, `score_prediction('2+2','4',0.9)`, and `calibration()`. Optional `investigate('A', local_model=OllamaProvider('installed-model'))` is native-first; provider proposals remain quarantined. All changes are restricted to predefined arithmetic routing; no dynamic code execution or automatic promotion of model assertions. The default policy is exact-v1. Read INCREMENT.md for limitations and inspect adaptive_experiment_26.json for actual benchmark outputs. Dashboard displays the bounded reflective report, not an automatic source-editing interface.

Local regression: `python -m unittest discover` (137 passed); inherited V5: `(cd v5 && python -m unittest discover)` (70 executions passed). Verify `sha256sum -c SHA256SUMS` from this directory. Previous releases are preserved. No independent validation or live model result is claimed.

## Alpha 0.27 — multi-domain adaptive reasoning

`m = Strategy(Application(core, None)).multidomain` exposes `cycle(activate=False, max_rounds=3)`, explicit `cycle(activate=True)`, `rollback('graph')`, `self_model()`, `hypotheses(['A','B'])`, and `retract_manual('A','source')`. Withdrawal queues downstream literal objectives; drain with `strategy.verified.continue_research()`. Optional `hypotheses([...], local_model=OllamaProvider('installed-model'))` performs native-first batch quarantine. The new `strategy.run('domain:'+json.dumps(task), native_only=True)` accepts arithmetic (`domain`, `expression`), isolated logic (`domain`, `facts`, `rules` as [premises, conclusion], `query`), or graph (`domain`, `edges` as [from,to], `start`, `target`). Example graph: `{"domain":"graph","edges":[["A","B"],["B","C"]],"start":"A","target":"C"}`; graph policy initially abstains until a successful explicitly activated cycle. Cycles do not alter prior routes. Dashboard exposes observational self-model. See INCREMENT.md and multidomain_experiment_27.json for actual results, scope and public seeds. Run `python -m unittest discover` (149 passed) and `(cd v5 && python -m unittest discover)` (70 passed inherited executions). Verify `sha256sum -c SHA256SUMS`. Separate synthetic holdout is not external independent validation; live Ollama probe unavailable.
