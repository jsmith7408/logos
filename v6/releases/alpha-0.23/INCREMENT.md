# Alpha 0.23 — Persistent investigation continuation

Planner.history returns bounded newest-first reports; Planner.resume re-evaluates the objective against current knowledge and links the previous investigation without overwriting it. Restart, newly supported conclusions, newly introduced contradictions, empty history and limits are tested. No provider calls are required. This is replay, not autonomous acquisition or checkpointed traversal. Concurrent writers remain unsupported; previous report links can branch. Offline model integration and semantic extraction remain pending. V5 is owner-authorized only; independent scientific, live-provider and external security validation remain outstanding.

Executed `python -m unittest discover -v`: 99 tests passed (28.192s). No fresh V5 run.
