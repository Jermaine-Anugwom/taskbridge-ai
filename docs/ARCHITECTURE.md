# Architecture

## Data flow

1. `WorkflowCreate` validates the captured interview.
2. `capture_workflow` scans untrusted text and creates evidence records.
3. `assess_workflow` scores four intervention choices and records reasons, risks, unknowns, and human checkpoints.
4. `explain_assessment` uses the same assessment evidence to produce four audience views.
5. A pilot selects one of three synthetic adapters and runs deterministic decisions.
6. Each decision retains a source record identifier and optional human checkpoint.
7. Optional model analysis emits a schema-bound tool call that is validated against workflow evidence.
8. SQLite or PostgreSQL stores workflows, assessments, pilots, fingerprinted runs, and model traces.
9. The handoff renderer creates a plain-text operating package.

## Trust boundaries

```mermaid
flowchart TB
  U[Untrusted interview or fixture] --> V[Schema validation]
  V --> P[Injection quarantine]
  P --> E[Evidence record]
  E --> D[Deterministic assessment]
  D --> S[Read-only pilot simulation]
  S --> R[Trace and measures]
  M[Optional model] -. advisory only .-> D
  X[External systems]:::blocked
  S -. no writes .-> X
  classDef blocked fill:#ffddd2,stroke:#c83c36,color:#7f261d
```

## Model boundary

`StructuredModel` is a narrow provider protocol. `DeterministicModel` is the default. `OpenAICompatibleModel` supports local Ollama or an explicitly configured compatible endpoint. The provider is forced through the `record_workflow_analysis` tool schema. Provider output is validated again locally and cannot weaken evidence or external-action restrictions.
