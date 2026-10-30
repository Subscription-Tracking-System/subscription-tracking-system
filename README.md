# Subscription Tracking System

Track recurring subscriptions in one place and see their combined monthly
commitment in TRY, USD, or EUR. The planned web interface supports Turkish and
English.

This branch contains the Sprint 1 project foundation: an API contract,
integration decisions, repository guidance, and automated contract checks.
It does not contain an implemented frontend, backend, or deployed service.

## First release scope

- Create, list, view, update, and delete user-owned subscriptions.
- Track MONTHLY or YEARLY billing and ACTIVE, PAUSED, or CANCELLED status.
- Keep each subscription's original TRY, USD, or EUR currency.
- Show the monthly equivalent in a selected base currency using fixed mock rates.
- Support TR/EN interface localization and localized API errors.
- Use a local authentication stub with the same boundary as a future provider.

Live banking, payment processing, automated cancellation, renewal notifications,
forecasts, appointments, and live exchange-rate integrations are deferred.

## Validate the contract

Use Python 3.12. Create and activate an isolated environment before installing
the pinned validation dependencies.

```sh
python -m venv .venv
```

Windows PowerShell activation: `.\.venv\Scripts\Activate.ps1`.
macOS/Linux activation: `source .venv/bin/activate`.
If local policy prevents activation, invoke the environment's Python directly.

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate_contract.py --report artifacts/contract-validation.json
python -m unittest discover -s tests -v
```

Validation rejects invalid OpenAPI, unresolved references, duplicate YAML keys,
invalid documented payloads, and mismatched HTTP/problem statuses. The acceptance
suite also checks required fields, ownership fields, currencies, lifecycle states,
timestamp formats, and empty PATCH requests. These are contract checks, not
evidence of working API endpoints or application test coverage.

## Project documents

| Document | Purpose |
| --- | --- |
| [OpenAPI contract](api/openapi.yaml) | Operations, security boundary, schemas, and examples |
| [Integration handoff](docs/sprint-1/integration-handoff.md) | Currency, localization, authentication, and API/UI coordination |
| [Scope reconciliation](docs/sprint-1/scope-reconciliation.md) | Differences from the existing API draft and decisions needing team review |
| [Furkan's contribution](docs/sprint-1/furkan-contribution.md) | Individual Sprint 1 work and verifiable evidence |
| [Contribution workflow](CONTRIBUTING.md) | Issue, branch, commit, PR, review, and ruleset guidance |
| [Monthly example fixture](api/examples/monthly-summary.json) | Synthetic inputs and expected totals for future implementation tests |
| [Contract CI](.github/workflows/contract.yml) | Repeatable checks on pull requests and integration branches |

## License

The repository currently contains the [MIT License](LICENSE). The supplied team
report names Apache License 2.0; the Product Owner must reconcile this difference
before submission. This contribution retains the existing license.
