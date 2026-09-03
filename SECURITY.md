# Security policy

## Demonstration boundary

TaskBridge runs against synthetic records and performs no external writes. The default engine is deterministic and credential-free. No customer, employee, financial, resume, or production data belongs in this repository.

## Controls

- Pydantic schemas reject unknown fields and invalid ranges.
- Imported text is treated as untrusted and scanned for instruction injection.
- The simulator records source identifiers with every decision.
- Unknown or contradictory information is held for review rather than inferred.
- Repeated pilot runs use stable fingerprints and cannot create duplicate records.
- Optional model credentials are read from environment variables and must never be committed.
- The public interface contains no model endpoint or privileged action.
- Production authentication stores SHA-256 token digests only. Raw bearer tokens remain in a secret manager or deployment secret.
- Viewer, operator, and administrator roles are enforced at the API boundary when `TASKBRIDGE_REQUIRE_AUTH=true`.
- Model traces exclude credentials and retain only evidence-safe prompts, hashes, usage, validation state, and output.

## Using optional model providers

Before connecting a model to non-synthetic information, confirm authorization, data classification, retention, geographic processing, access control, logging, incident response, and deletion requirements. A configured model remains advisory and may not change the deterministic safety boundary. Invalid schemas, unknown evidence IDs, unsupported numbers, timeouts, and provider errors fall back to human review.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use GitHub private vulnerability reporting when available.
