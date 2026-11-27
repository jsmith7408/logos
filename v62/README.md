# LOGOS V6.2 — multi-model capture candidate

Four adapters: OpenAI Responses, xAI Responses (Grok), Gemini generateContent, and local Ollama chat. Set model identifiers explicitly for models available in your accounts. No subscription credential is embedded. The provider APIs may bill separately from consumer subscriptions.

From repository root:

    python -m unittest v62.test_collect -v
    python -m v62 --db research.db --prompt "What is 6*7?" --provider openai=YOUR_MODEL --provider gemini=YOUR_MODEL --allow-network

Set OPENAI_API_KEY, GEMINI_API_KEY, or XAI_API_KEY through your local secret manager/environment as appropriate. Never commit credentials. Ollama must already be running on loopback port 11434 with the selected model installed.

The collector can share a database with V6 research records; its tables are separate. It captures the same prompt independently across up to four requested provider/model pairs, with output caps, fixed endpoints, no automatic retries, disabled redirects and direct network connections. Timeouts are socket timeouts, not guaranteed total wall-clock deadlines. A crash can leave pending rows; do not automatically retry. HTTP failures record error categories, not error response bodies. Successful HTTP bodies are stored as exact bytes, with SHA-256 digests. The request digest covers endpoint and payload, not headers. Credentials are excluded from stored request metadata; raw response bodies may contain sensitive information, so keep databases private. Storage is not tamper-proof.

Text equality is not truth, and unequal text is not necessarily semantic disagreement. No provider output is executed, automatically trusted, or signed as independent evidence. V5 signed study comparisons remain a separate gate with externally authorized study bindings and signers; automatic enrollment and certification are deliberately excluded. This is not a trained or self-modifying model.

Live connectivity and model compatibility require real credentials and a smoke test. The unit tests use mocked transports; they do not establish actual provider inference or scientific superiority.

API references:
- https://platform.openai.com/docs/api-reference/responses/create
- https://ai.google.dev/api/generate-content
- https://docs.x.ai/developers/rest-api-reference/inference/chat
- https://docs.ollama.com/api/chat
