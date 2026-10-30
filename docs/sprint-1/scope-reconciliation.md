# Sprint 1 scope reconciliation

The supplied Team 5 report defines a bilingual, multi-currency Subscription
Tracking System. The existing API draft in PR #8 adds appointment booking,
reminders, weekly billing, token-bound currency, and a different spending
calculation. This revision aligns the API with the report's subscription project
scope. The differences are explicit below so the architect and Product Owner
can review them before merge.

## Contract changes from the existing draft

| Area | PR #8 draft at e7812b2 | This first-release draft |
| --- | --- | --- |
| Product | Subscription and appointment system | Subscription Tracking System |
| Currency | Subscription currency must equal a token claim | Original TRY/USD/EUR accepted; summary base currency is independent |
| Summary | `/reports/spending?month=...` | `/dashboard/summary?baseCurrency=...` |
| Yearly prices | Repository issue #5 counts only the renewal month | Divide by 12 for a normalized monthly equivalent |
| Billing cycles | MONTHLY, YEARLY, WEEKLY | MONTHLY and YEARLY |
| Language | No locale parameter | TR/EN error localization through Accept-Language |
| Authentication | Login operation and token-bound base currency | Bearer boundary with a documented local stub; no implemented provider |
| Appointments | Booking, rescheduling, confirmation, cancellation | Outside the supplied project's first release |
| Reminders | Reminder endpoints and notification scheduler | Deferred according to the report |
| Concurrency | ETag and required If-Match | Deferred architectural decision; not promised by the report |
| Resource history | Dedicated history endpoint | CANCELLED retains the record; a separate audit endpoint is deferred |

This is a proposed contract revision, not evidence that the team has approved
or implemented every change. Preserve the original PR and author history.

## Decisions requiring team review

| Decision | Review owner | Current status |
| --- | --- | --- |
| Approve alignment to the report and coordinate the API PR | Ece, with Product Owner consultation | Pending teammate review |
| Reconcile existing GitHub story IDs with the report's US-01 to US-06 | Berrin Şule | Pending; existing issues have not been renamed |
| Choose one open-source license: repository MIT vs report Apache 2.0 | Berrin Şule, with technical review | Pending; existing LICENSE retained |
| Define duplicate-name case/whitespace normalization | Berrin Şule and Ece | Pending; the contract promises same-name conflict only |
| Document authentication stub issuance and verification | Ece | Boundary defined; issuance details pending |
| Approve draft validation choices: nonblank names, unknown fields rejected, null PATCH rejected, exact two-locale header support | Ece | Encoded in this draft; pending review |
| Approve fixed mock-rate fixture and final-sum rounding | Ece | Proposed deterministic fixture; pending review |
| Enable required checks and branch rules in GitHub | Mona and the authorized repository administrator | Workflow supplied; remote ruleset state not verified |

The implementation stack is deliberately left open. Python here is a validation
toolchain and does not choose the application's frontend or backend technology.
