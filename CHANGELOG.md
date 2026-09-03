# Changelog

## 0.2.1 - 2026-09-03

- Fixed missing provider usage being incorrectly recorded as zero.
- Preserved per-attempt provider, model, retries, and reported consumption through schema/evidence rejection and deterministic fallback.
- Distinguished complete usage totals from known partial subtotals; invalid or missing rates never fabricate a cost.
- Added fail-closed production configuration, distinct role-token validation, non-demo database credentials, and loopback port bindings.
- Added real PostgreSQL CI integration tests and loopback HTTP transport tests.
- Added a reproducible zero-network evaluation and explicit opt-in live-provider protocol. No live provider benchmark was executed.
- Documented that mechanical evidence checks do not prove semantic support.

## 0.2.0 - 2026-09-03

- Added an OpenAI-compatible model path with a forced structured tool contract.
- Added evidence and unsupported-number validation, retries, fallback, and auditable model traces.
- Added role-gated API access and PostgreSQL support for deployed operation.
- Added the Operate workshop stage for provider, schema, authority, latency, token, cost, and fallback inspection.
- Replaced the development web container with a static production image.

## 0.1.0 - 2026-09-02

- Added evidence-bound workflow interviews and four-way intervention assessment.
- Added shared-inbox, weekly-status, and invoice-exception scenario adapters.
- Added deterministic pilot simulation, audience explanations, measurement, and handoff output.
- Added the responsive TaskBridge workshop interface and credential-free static demonstration.
- Added security, accessibility, API, simulation, and regression tests.
