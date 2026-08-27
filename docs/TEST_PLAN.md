# SportsHub Test Plan

This plan verifies the CS425-sized SportsHub product. Tests should prove the school-project behavior without introducing features that are outside scope.

## Release gates

| Layer | What it must prove | Runs where | Gate |
| --- | --- | --- | --- |
| Static checks | TypeScript, Python, formatting, imports, and production web compilation are valid | Developer machine and CI | Every change |
| Backend API | Authentication, authorization, validation, stable IDs, idempotency, and provider-error behavior | Fast isolated database | Every change |
| Frontend component | Route protection, forms, loading/empty/error states, authorization headers, and optimistic rollback | Vitest + Testing Library | Every change |
| PostgreSQL integration | Alembic can build the schema and repository behavior matches PostgreSQL | Docker test database | Every pull request |
| Browser journey | A fan can register, follow a team, open the in-app alert inbox, and retain read state after refresh | Desktop and mobile Chromium | Every pull request once the journey exists |
| Operational smoke | Containers become healthy, migrations run once, data survives an API restart, and logs contain no secrets | Docker Compose | Before a tagged release |

## Current acceptance coverage

- Register and log in with a bearer token; reject duplicate identities and incorrect credentials.
- Protect `/teams` and `/alerts` in the browser.
- Search teams and return stable internal IDs even when the provider uses external IDs.
- Append missing user-team associations without duplicating an existing follow.
- Remove only the authenticated user's team association after confirmation, without deleting the shared team or another user's follow.
- Authenticate preference operations from the bearer token; never accept browser-supplied `userId`.
- Commit team follows and their corresponding inbox records atomically.
- Scope inbox records and read operations to the authenticated user; keep push delivery outside the current fan-facing workflow.
- Return a useful error when an external team provider fails.
- Apply and reverse the initial Alembic revision.
- Report liveness separately from database readiness.

## Coverage to add with each web milestone

### Fixtures and sports browsing

- Competition, fixture, team, and player response contracts.
- Provider normalization, cache hit/miss, stale data, timeout, quota, and partial-data behavior.
- Loading, no-results, unavailable-provider, and accessible table/card states.

### Live match

- Independent poller change detection and broadcast criteria.
- Subscribe-before-snapshot ordering, connected/detail/update events, heartbeat, and cleanup.
- Reconnect receives fresh current state; assert that event replay and `Last-Event-ID` are absent.
- Multiple fixture subscriptions do not leak events across fans.

### Tickets

- Fixture-to-Ticketmaster parameter resolution and attraction-mapping sentinel behavior.
- Empty Ticketmaster result handling and cached event results.
- `/api/v1/tickets/events/{eventId}/buy` chooses Impact only when eligible and falls back on gateway failure.
- No payment, inventory, fulfillment, or durable `TicketOffer` behavior exists in SportsHub.

### Administration and operations

- Role checks for every admin operation and negative tests for ordinary fans.
- Migration upgrade from the previous release, backup/restore rehearsal, and secret redaction.
- Accessibility keyboard flow, focus states, labels, color contrast, responsive layouts, and performance budgets.

## Standard commands

```bash
make test
make test-integration
cd sportshub-frontend && npm run lint && npm run build && npm run test:e2e
docker compose config --quiet
```

Test data must be synthetic. The integration suite uses `sportshub_test`; it must never target the development or production database.
