# Reproducible reliability evaluation

This corpus measures accounting and safety-boundary behavior, not customer outcomes or model intelligence. Everything is synthetic. The default evaluation makes **zero provider requests** and does not load model credentials.

```bash
python -m taskbridge.evaluate --check
```

The committed [offline report](offline-results.json) records the dataset version/hash, schema and prompt versions, and each case's expected behavior. It covers reported, missing, zero and partial usage; unknown evidence; unsupported numbers; missing approval; timeout; schema rejection; retries; deterministic operation; and a semantic counterexample. The corpus hash includes the complete synthetic workflows and expected outcomes. Repeated offline runs produce the same report.

The semantic counterexample is intentionally important: nonnumeric invented prose can cite an existing evidence ID and pass mechanical validation. Its recorded success means the mechanical validator accepted it, **not** that the statement is true. Human semantic review remains mandatory.

## Evidence levels

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Offline scripted cases | Accounting invariants and boundary regressions | Live provider behavior |
| Real loopback HTTP tests | Client transport, serialization, retries and rejected-response usage | Provider compatibility or model quality |
| Real PostgreSQL CI service | Persistence, rollback, uniqueness, concurrent writes and API roles | A hosted production deployment |
| Live provider benchmark | **NOT RUN** | No live latency, cost or quality claims are made |

## Optional live protocol, not run as part of this release

A future operator may configure an approved endpoint/model and deliberately invoke:

```bash
python -m taskbridge.evaluate --mode live --allow-provider-requests --check
```

This mode can incur provider charges. Do not run it under a zero-spend constraint. It requires an explicitly configured HTTP provider, uses exactly three fixed synthetic workflows, disables retries, and limits each response to 1,600 output tokens. It records actual timestamps, model identity, prompt fingerprint, returned usage, attempts, latency, and configured-rate estimates. Missing usage or rates remain unknown. Provider errors and validation failures are retained and cause `--check` to fail; they are not replaced by a success claim.

Before publishing a live result, inspect every claim against its cited statements, record supported/unsupported/ambiguous judgments, check for prompt leakage or sensitive provider output, and retain failures. No live run can be described as semantically validated while `semantic_review` is `PENDING_HUMAN_REVIEW`.

Do not publish API keys, endpoint credentials, private workflow records, or unreviewed output. No release script automatically runs or publishes a live benchmark.
