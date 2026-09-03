# Local runbook

## Start

```bash
docker compose up --build
```

- Workshop: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8000`
- API health: `http://127.0.0.1:8000/health`

## Verify

```bash
python -m pip install -c constraints.txt -e '.[dev]'
ruff check .
pytest -q
cd web
npm ci
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

## Reset local state

Stop the containers and remove only the local `taskbridge.db` file. Fixture files are immutable source data and should not be edited during a run.

The Compose database lives in a PostgreSQL volume, not `taskbridge.db`. Do not remove a volume to troubleshoot or test restoration; use a separate disposable test schema instead.

## Production configuration (not deployed by this repository)

Use `docker compose -f compose.production.yaml config --quiet` to validate the separate production configuration. It requires a strong URL-safe `TASKBRIDGE_POSTGRES_PASSWORD` (at least 16 characters) and three distinct SHA-256 token digests. Generate random bearer tokens locally, retain the raw values only in a secret store, and configure only their lowercase digests. Never copy demo credentials into production.

Production startup fails before the database is opened if `TASKBRIDGE_REQUIRE_AUTH` is not `true`, a role digest is missing, malformed or duplicated, or the database configuration uses a demo password. Production requests still require authentication even if the flag is later misconfigured. Loopback ports need a separately secured TLS reverse proxy for remote access. TLS, rotation, backups, rate limits, and operational monitoring require a separate deployment review. The template remains deterministic and cannot incur model fees by default.

## Real PostgreSQL verification

CI provisions a disposable PostgreSQL 17 service on the public repository's standard runner. It does not create a paid database or contact an existing server. Tests use the loopback `taskbridge_test` database and create a unique schema per test, then remove only that schema. They cover reconnect persistence, null-usage traces, concurrent upserts, rollback, fingerprint uniqueness, ordering, and production API roles.

For an already installed local test PostgreSQL, set `TASKBRIDGE_TEST_POSTGRES_URL` to that loopback test database and run `pytest -q tests/test_postgres.py`. `TASKBRIDGE_REQUIRE_POSTGRES_TESTS=true` makes missing configuration a failure rather than a skip. Do not supply a production DSN.

## Zero-spend evaluation

Run `python -m taskbridge.evaluate --check`. It uses synthetic fixtures without loading provider credentials or making provider requests. Read [the protocol](evaluations/README.md) before any explicitly authorized live run. A live benchmark is not an acceptance claim until its actual results have been inspected.

## Failure handling

- Invalid workflow input: preserve the validation response and correct the source record.
- Injection detection: quarantine the record; do not copy its instructions into another prompt.
- Optional model outage: confirm the trace records a fallback, keep external actions disabled, and investigate the provider outside the workflow path.
- Invalid model schema or evidence citation: preserve the blocked trace category and do not retry with looser validation.
- Cost missing: leave cost as unknown until approved provider rates are configured. Never infer pricing.
- Authentication failure: verify the deployment secret and stored digest. Never log or paste a bearer token into an issue.
- Duplicate run fingerprint: return the existing result.
- Missing source evidence: stop the assessment or mark the missing information for review.
