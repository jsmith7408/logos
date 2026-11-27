# Native LOGOS runtime

Current main release: Alpha 0.30. Alpha 0.31 remains an experimental development candidate, not a merged release.

## Run locally

From the repository root, enter v6. Use Python 3 and install the V5 cryptography dependency in an isolated environment if needed. No external model server, API key or pretrained weights are required for native inference.

    cd v6
    python logos_native.py status
    python logos_native.py chat "calculate 2+2"
    python -m unittest discover
    (cd v5 && python -m unittest discover)
    sha256sum -c SHA256SUMS

For native training, checkpoint admission and rollback, see the first Alpha 0.30 section of [the release instructions](v6/README.md). All older provider setup instructions are historical and must not be followed.

## Policy

Web access is for evidence retrieval only. Legacy OllamaProvider and DeadlineProvider interfaces are retained for compatibility and reject inference. Do not enable them. Generated language and experimental records are not verified facts. V5 is owner-authorized, not independently certified.

Historical reports and regression logs are being relocated under v6/archive on the cleanup branch. Original release snapshots are preserved. Full cleanup regression and link checks remain pending.
