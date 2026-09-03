# Model operations

TaskBridge can call an approved OpenAI-compatible model endpoint without giving the model authority over the workflow. The model receives a versioned system instruction, a user task, and captured evidence statements. It must return a call to `record_workflow_analysis` using the schema generated from `StructuredModelOutput`.

## Output contract

The tool call contains:

- A summary with supporting evidence IDs.
- Evidence-bound observations with confidence.
- Optional `hold_for_review` or `draft_pilot_note` proposals.
- An explicit abstention state and reason.

Tool proposals are records, not executions. `requires_approval` must remain true. TaskBridge rejects unknown evidence IDs and numeric claims that do not appear in the cited evidence statements.

## Runtime trace

Each call records:

- Provider and returned model identifier.
- Prompt and schema versions.
- SHA-256 prompt fingerprint.
- Latency and retry count.
- Input and output tokens.
- Cost only when approved input and output rates are configured.
- Success, fallback, or blocked state.
- A non-sensitive provider error category when fallback occurs.

Credentials never enter the trace. The public workshop contains a committed synthetic trace rather than an active paid-model connection.

## Failure behavior

Transient HTTP and network failures retry with a short bounded backoff. A final provider failure, invalid response, unsupported claim, or bad evidence reference returns the deterministic fallback. The fallback abstains and proposes human review. It cannot execute an external action.

## Local configuration

Set `TASKBRIDGE_MODEL_PROVIDER=openai_compatible`, the endpoint, model name, and API key through deployment secrets. Use `TASKBRIDGE_MODEL_PROVIDER=ollama` for an OpenAI-compatible local Ollama endpoint. Published provider rates are optional; cost remains unknown when either rate is missing.
