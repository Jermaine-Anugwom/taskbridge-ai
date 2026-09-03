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

## Failure handling

- Invalid workflow input: preserve the validation response and correct the source record.
- Injection detection: quarantine the record; do not copy its instructions into another prompt.
- Optional model outage: confirm the trace records a fallback, keep external actions disabled, and investigate the provider outside the workflow path.
- Invalid model schema or evidence citation: preserve the blocked trace category and do not retry with looser validation.
- Cost missing: leave cost as unknown until approved provider rates are configured. Never infer pricing.
- Authentication failure: verify the deployment secret and stored digest. Never log or paste a bearer token into an issue.
- Duplicate run fingerprint: return the existing result.
- Missing source evidence: stop the assessment or mark the missing information for review.
