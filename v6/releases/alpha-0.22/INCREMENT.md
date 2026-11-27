# Alpha 0.22 — Native research planner

Adds Planner integrated through Strategy.planner: persistent objectives and reports, arithmetic/scoped inference/abstention routing, bounded premise traversal, conditional hypotheses with existing local support, and gap detection. No provider calls or automatic fact promotion. Local support is not authenticated evidence. Explicit literals only; no external acquisition, learned planning, dashboard integration, or wall-clock guarantee. Each run is bounded by 32 checks, 10,000 inference steps per check and bounded rule scans. Reports are snapshots, not atomic across concurrent knowledge writers; trusted single-user operation only.

Executed `python -m unittest test_planner -v` (9/9) and `python -m unittest discover -v` (95/95, 27.986s). No fresh V5 run. Independent validation remains outstanding.
