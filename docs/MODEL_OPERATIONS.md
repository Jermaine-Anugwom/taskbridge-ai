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

Credentials never enter the trace. The public workshop contains a committed synthetic trace rather than an active paid-model connection. It is not a live usage dashboard.

### Attempt accounting (0.2.1)

`attempts` retains each primary request and fallback separately, including provider/model identity, retry index, latency, reported usage, and non-sensitive error category. Usage is captured before schema validation. An invalid schema or evidence reference cannot erase the original response's consumption. Rejected raw output and provider error bodies are not recorded.

Missing, malformed, or negative token counts become `null`, never zero. An explicitly reported zero remains zero. `usage` totals a field only if it is known for every attempt; `reported_usage` sums only known values and is explicitly incomplete when any attempt is unknown. A timeout may still be billable. Retries therefore do not turn a partially known total into a misleading complete total.

Cost is a configured-rate estimate, not an invoice. It stays unknown if usage or valid rates are missing. The built-in deterministic path has zero provider consumption, but does not make prior unknown consumption free. The top-level provider/model identifies the selected output; the attempt ledger identifies every recorded provider call.

Historical v0.2.0 traces cannot recover usage that was never captured. They remain historical records; an empty attempt list must not be presented as newly verified accounting.

### Validation limits

The validator checks evidence identifiers, numeric overlap, tool names, and approval flags. It does **not** establish semantic entailment. A plausible but unsupported nonnumeric statement can cite a real evidence ID and pass these mechanical checks. `semantic_review_required` remains true. The evaluation includes this counterexample rather than claiming zero unsupported prose.

## Failure behavior

Transient HTTP and network failures retry with a short bounded backoff. A final provider failure, invalid response, mechanically detected unsupported number, or bad evidence reference returns the deterministic fallback. The fallback abstains and proposes human review. It cannot execute an external action.

## Local configuration

Set `TASKBRIDGE_MODEL_PROVIDER=openai_compatible`, the endpoint, model name, and API key through deployment secrets. Use `TASKBRIDGE_MODEL_PROVIDER=ollama` for an OpenAI-compatible local Ollama endpoint. Published provider rates are optional; cost remains unknown when either rate is missing.

See [Evaluation protocol](../evaluations/README.md) for the offline accounting corpus and explicitly opt-in provider run. No live provider is invoked by default or by CI.
