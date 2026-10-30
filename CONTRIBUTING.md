# Contribution workflow

Every assessed contribution should be traceable from a named issue to a branch,
commit, reviewed pull request, and sprint release. Use an individual GitHub account.

## Start from an issue

Record the purpose, owner, acceptance criteria, and affected API or documents.
Story IDs in the supplied Word report differ from the current GitHub issues;
link the actual issue URL rather than assuming the numbers are interchangeable.
The Product Owner owns reconciliation of the product backlog.

## Branches and commits

- `main`: reviewed, assessed releases.
- `develop`: reviewed work for the next release.
- `feature/<issue-number>-<short-name>`: one focused contribution.
- `release/*` and `hotfix/*`: optional when an actual need exists.

Normally create feature branches from current `develop`. Reference the real
issue number in commits, for example `docs: clarify subscription ownership (#7)`.
Do not push directly to `main` or `develop`.

### Existing API draft dependency

This contribution's `feature/7-sprint1-contract-alignment` branch starts at
`e7812b2`, the existing `feature/7-openapi-contract` branch from PR #8. This keeps
the original author's commit and makes the scope changes reviewable against that
draft. The intended first PR base is `feature/7-openapi-contract`; once reviewed
there, PR #8 continues into `develop`. This is a documented exception to the
usual branch-from-develop rule, not a replacement of the original author's work.

Before publishing, fetch and compare the current remote API branch. If another
teammate has changed it, integrate their work and rerun validation. Never
force-push another member's branch.

## Pull requests

Include the linked issue, reason for the change, behavior or contract differences,
validation commands and results, and any decisions requiring approval. Request
at least one teammate's review before merging. A green schema check does not
constitute architectural approval or an implementation test.

For the Sprint 1 contract contribution, review the first-release scope with Ece,
the CI configuration with Mona, the process evidence with Meriç, and unresolved
scope or license decisions with Berrin Şule. These review areas supplement the
team's RACI matrix rather than replacing it.

## Proposed GitHub ruleset for main and develop

An authorized repository administrator should configure and verify:

1. Pull requests required for changes.
2. At least one approving review, with stale approvals dismissed after changes.
3. Required status check: the `Validate OpenAPI and contract acceptance cases`
   job emitted by `Contract CI`, selected after its first successful GitHub run.
4. Force pushes and branch deletion blocked.
5. Bypass permissions limited to the team's agreed administrative policy.

These are configuration instructions. A committed workflow alone does not prove
that a ruleset is enabled. Keep a ruleset screenshot or authorized settings link
as separate sprint evidence. Contract CI intentionally has no path filters, so
a required check will also run on documentation-only PRs.

## Before submission

- Run the validator and acceptance suite with the pinned dependencies.
- Keep actual issue, PR, commit, and CI run links.
- Complete teammate review and resolve scope questions.
- Have the release owner create the assessed `sprint-1` tag on reviewed work.
- Keep the repository history intact for individual contribution assessment.

## References

- [OpenAPI 3.1.0 specification](https://spec.openapis.org/oas/v3.1.0)
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
